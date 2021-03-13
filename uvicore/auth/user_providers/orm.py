import uvicore
from uvicore.auth.user import User
from uvicore.support.hash import sha1
from uvicore.contracts import UserProvider
from uvicore.support.dumper import dump, dd
from uvicore.auth.support import password as pwd
from uvicore.http.request import HTTPConnection
from uvicore.typing import List, Union, Any, Dict
from uvicore.auth.models.user import User as Model


@uvicore.service()
class Orm(UserProvider):
    """Retrieve and validate user from uvicore.auth ORM User model during Authentication middleware

    This is NOT a stateless user provider as it queries the user, groups, roles tables from a database.
    """

    def __init__(self):
        # Only need for an __init__ override is to modify field mappings
        super().__init__()

        # Temp, until I add username to ORM model
        self.field_map['username'] = 'email'

    async def _retrieve_user(self,
        key_name: str,
        key_value: Any,
        request: HTTPConnection,
        *,
        password: str = None,

        # Parameters from auth config
        anonymous: bool = False,
        includes: List = None,

        # Must have kwargs for infinite allowed optional params, even if not used.
        **kwargs,
    ) -> User:

        # Get password hash for cache key.  Password is still required to pull the right cache key
        # or else someone could login with an invalid password for the duration of the cache
        password_hash = '/' + sha1(password) if password is not None else ''

        # Check if user already validated in cache
        cache_key = 'auth/user/' + str(key_value) + password_hash
        if await uvicore.cache.has(cache_key):
            # User is already validated and cached
            # Retrieve user from cache, no password check required because cache key has password has in it
            user = await uvicore.cache.get(cache_key)
            return user

        # Cache not found.  Query user, validate password and convert to user class
        # ORM is currently thworing a Warning: Truncated incorrect DOUBLE value: '='
        # when using actual bool as bit value.  So I convert to '1' or '0' strings instead
        disabled = '1' if anonymous else '0'
        kwargs = {key_name: key_value}
        db_user = await (Model.query()
            .include(*includes)
            .where('disabled', disabled)
            .show_writeonly(['password'])
            .find(**kwargs)
        )

        # User not found or disabled.  Return None means not verified or found.
        if not db_user: return None

        # If password, validate credentials
        if password is not None:
            if not pwd.verify(password, db_user.password):
                # Invalid password.  Return None means not verified or found.
                return None

        # Get users groups->roles->permissions (roles linked to a group)
        groups = []
        roles = []
        permissions = []
        if 'groups' in includes:
            user_groups = db_user.groups
            if user_groups:
                for group in user_groups:
                    groups.append(group.name)
                    if not group.roles: continue
                    for role in group.roles:
                        roles.append(role.name)
                        if not role.permissions: continue
                        for permission in role.permissions:
                            permissions.append(permission.name)

        # Get users roles->permissions (roles linked directly to the user)
        if 'roles' in includes:
            user_roles = db_user.roles
            if user_roles:
                for role in user_roles:
                    roles.append(role.name)
                    if not role.permissions: continue
                    for permission in role.permissions:
                        permissions.append(permission.name)

        # Unique groups, roles and permissions (sets are unique)
        groups = sorted(list(set(groups)))
        roles = sorted(list(set(roles)))
        permissions = sorted(list(set(permissions)))

        # Set super admin, existence of 'admin' permission
        superadmin = False
        if 'admin' in permissions:
            # No need for any permissinos besides ['admin']
            permissions = ['admin']
            superadmin = True

        # Build UserInfo dataclass with REQUIRED fields
        user = User(
            id=db_user.id,
            uuid=db_user.uuid,
            username=db_user.email,
            email=db_user.email,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            title=db_user.title,
            avatar=db_user.avatar_url,
            groups=groups,
            roles=roles,
            permissions=permissions,
            superadmin=superadmin,
            authenticated=True,
        )

        # Save to cache
        await uvicore.cache.put(cache_key, user, seconds=10)

        # Return to user
        return user



    # These two are temporary to overwrite username to email field
    # Once I add username to ORM model, I can remove these and use the interfaces defaults

    # async def retrieve_by_username(self, username: str, request: HTTPConnection, **kwargs) -> User:
    #     """Retrieve the user by username from the user provider backend.  No validation."""
    #     return await self._retrieve_user('email', username, request, **kwargs)

    # async def retrieve_by_credentials(self, username: str, password: str, request: HTTPConnection, **kwargs) -> User:
    #     """Retrieve the user by username from the user provider backend AND validate the password if not None"""
    #     return await self._retrieve_user('email', username, request, password=password, **kwargs)