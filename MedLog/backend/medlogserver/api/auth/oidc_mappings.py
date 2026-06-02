from typing import TYPE_CHECKING

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.user import User, UserUpdateByAdmin
from medlogserver.model.user_info_oidc import UserInfoOidc

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
    to the user on every login (issues #273, #46, and #308)."""
    user_groups = userinfo.groups or []

    # --- Issue #308: re-sync profile fields from OIDC userinfo on every login ---
    new_display_name = userinfo.name or user.display_name
    new_email = userinfo.email or user.email
    if (
        new_display_name != user.display_name
        or new_email != user.email
        or userinfo.email_verified != user.is_email_verified
    ):
        log.info(f"Updating profile for user '{user.user_name}' via OIDC userinfo sync")
        user = await user_crud.update(
            UserUpdateByAdmin(
                display_name=new_display_name,
                email=new_email,
                is_email_verified=userinfo.email_verified,
            ),
            user_id=user.id,
        )

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

    # --- Issues #46 + #305: apply study permission mapping with source tracking ---
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

        oidc_managed_flags = {
            p
            for permissions in group_permission_map.values()
            for p in permissions
            if p in _VALID_STUDY_PERMISSIONS
        }
        unknown = granted_permissions - _VALID_STUDY_PERMISSIONS
        if unknown:
            log.warning(
                f"STUDY_PERMISSION_MAPPING for study '{study_name}' contains unknown "
                f"permission(s) {unknown} — ignoring"
            )
        valid_granted = granted_permissions & oidc_managed_flags

        log.info(
            f"OIDC permission sync for user '{user.user_name}' in study '{study_name}': "
            f"managed={oidc_managed_flags} granted={valid_granted}"
        )
        await study_permission_crud.oidc_set_permissions(
            user_id=user.id,
            study_id=study.id,
            oidc_managed_flags=oidc_managed_flags,
            valid_granted=valid_granted,
        )

    return user
