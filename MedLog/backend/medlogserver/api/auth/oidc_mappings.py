from typing import TYPE_CHECKING

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.user import User, UserUpdateByAdmin
from medlogserver.model.user_info_oidc import UserInfoOidc
from medlogserver.model.study_permission import StudyPermissonUpdate

if TYPE_CHECKING:
    from medlogserver.db.user import UserCRUD
    from medlogserver.db.study import StudyCRUD
    from medlogserver.db.study_permission import StudyPermissonCRUD

log = get_logger()
config = Config()

_VALID_STUDY_PERMISSIONS = {"is_study_interviewer", "is_study_viewer", "is_study_admin"}


async def apply_oidc_group_mappings(
    user: User,
    userinfo: UserInfoOidc,
    provider_config: Config.OpenIDConnectProvider,
    user_crud: "UserCRUD",
    study_permission_crud: "StudyPermissonCRUD",
    study_crud: "StudyCRUD",
) -> User:
    """Re-apply ROLE_MAPPING and STUDY_PERMISSION_MAPPING from the OIDC provider config
    to the user on every login (issues #273 and #46)."""
    user_groups = userinfo.groups or []

    # --- Issue #273: re-apply global role mapping ---
    available_medlog_roles = [config.ADMIN_ROLE_NAME, config.USERMANAGER_ROLE_NAME]
    new_roles = [r for r in user_groups if r in available_medlog_roles]
    for oidc_group, mapping_roles in provider_config.ROLE_MAPPING.items():
        if oidc_group in user_groups:
            new_roles.extend(mapping_roles)
    new_roles = list(set(new_roles))

    if set(new_roles) != set(user.roles or []):
        log.info(
            f"Updating roles for user '{user.user_name}' via OIDC group mapping: {new_roles}"
        )
        user = await user_crud.update(
            UserUpdateByAdmin(roles=new_roles),
            user_id=user.id,
        )

    # --- Issue #46: apply study permission mapping ---
    for study_name, group_permission_map in provider_config.STUDY_PERMISSION_MAPPING.items():
        study = await study_crud.get_by_name(study_name)
        if study is None:
            log.warning(
                f"STUDY_PERMISSION_MAPPING references unknown study '{study_name}' — skipping"
            )
            continue

        granted_permissions = set()
        for oidc_group, permissions in group_permission_map.items():
            if oidc_group in user_groups:
                granted_permissions.update(permissions)

        if not granted_permissions:
            continue

        perm_kwargs = {p: True for p in granted_permissions if p in _VALID_STUDY_PERMISSIONS}
        unknown = granted_permissions - _VALID_STUDY_PERMISSIONS
        if unknown:
            log.warning(
                f"STUDY_PERMISSION_MAPPING for study '{study_name}' contains unknown "
                f"permission(s) {unknown} — ignoring"
            )
        if not perm_kwargs:
            continue

        log.info(
            f"Applying study permissions {perm_kwargs} for user '{user.user_name}' "
            f"in study '{study_name}' via OIDC group mapping"
        )
        await study_permission_crud.update_or_create_if_not_exists(
            user_id=user.id,
            study_id=study.id,
            study_permission=StudyPermissonUpdate(**perm_kwargs),
        )

    return user
