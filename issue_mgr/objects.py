import enum


@enum.unique
class Role(enum.IntEnum):
    # NB: When new roles are added, the user_BEFORE_INSERT and user_BEFORE_UPDATE triggers should be updated to accept the new role values
    admin = 0
    student = 1
    teacher = 2
