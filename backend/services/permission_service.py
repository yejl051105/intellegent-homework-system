"""角色 → 前端路由的权限配置。

前端不写死页面路由：登录后调用 /api/routes 拿到本角色可访问的路由表，
再按 component 字段（对应 views/ 下的组件文件名）动态注册。
meta 中的 nav / icon / order / activePrefixes 驱动顶部导航的渲染与高亮。
新增页面时在这里加一条记录即可，无需改前端路由代码。
"""
from copy import deepcopy


ROLE_ROUTE_CONFIG = {
    "student": {
        "home": "/student/dashboard",
        "routes": [
            {
                "path": "/student/dashboard",
                "name": "StudentDashboard",
                "component": "StudentDashboard",
                "meta": {
                    "role": "student",
                    "title": "我的作业",
                    "icon": "Collection",
                    "nav": True,
                    "order": 10,
                    "activePrefixes": ["/student/dashboard", "/student/homework/"],
                },
            },
            {
                "path": "/student/homework/:id",
                "name": "StudentHomeworkDetail",
                "component": "StudentHomeworkDetail",
                "meta": {"role": "student", "title": "作业详情"},
            },
            {
                "path": "/student/upload",
                "name": "StudentUpload",
                "component": "StudentUpload",
                "meta": {
                    "role": "student",
                    "title": "提交作业",
                    "icon": "UploadFilled",
                    "nav": True,
                    "order": 20,
                    "keepAlive": True,
                    "activePrefixes": ["/student/upload"],
                },
            },
            {
                "path": "/student/exemplary",
                "name": "StudentExemplary",
                "component": "StudentExemplary",
                "meta": {
                    "role": "student",
                    "title": "优秀作业",
                    "icon": "TrophyBase",
                    "nav": True,
                    "order": 30,
                    "activePrefixes": ["/student/exemplary"],
                },
            },
            {
                "path": "/student/exemplary/:id",
                "name": "StudentExemplaryDetail",
                "component": "ExemplaryDetail",
                "meta": {"role": "student", "title": "优秀作业详情"},
            },
            {
                "path": "/student/recycle-bin",
                "name": "StudentRecycleBin",
                "component": "RecycleBin",
                "meta": {
                    "role": "student",
                    "title": "回收站",
                    "icon": "Delete",
                    "nav": True,
                    "order": 40,
                    "activePrefixes": ["/student/recycle-bin"],
                },
            },
        ],
    },
    "teacher": {
        "home": "/teacher/dashboard",
        "routes": [
            {
                "path": "/teacher/dashboard",
                "name": "TeacherDashboard",
                "component": "TeacherDashboard",
                "meta": {
                    "role": "teacher",
                    "title": "全部作业",
                    "icon": "Files",
                    "nav": True,
                    "order": 10,
                    "activePrefixes": ["/teacher/dashboard", "/teacher/grade/"],
                },
            },
            {
                "path": "/teacher/grade/:id",
                "name": "TeacherGrade",
                "component": "TeacherGrade",
                "meta": {"role": "teacher", "title": "作业评分"},
            },
            {
                "path": "/teacher/criteria",
                "name": "TeacherCriteria",
                "component": "TeacherCriteria",
                "meta": {
                    "role": "teacher",
                    "title": "评分标准",
                    "icon": "Tickets",
                    "nav": True,
                    "order": 20,
                    "keepAlive": True,
                    "activePrefixes": ["/teacher/criteria"],
                },
            },
            {
                "path": "/teacher/exemplary",
                "name": "TeacherExemplary",
                "component": "TeacherExemplary",
                "meta": {
                    "role": "teacher",
                    "title": "优秀作业",
                    "icon": "Medal",
                    "nav": True,
                    "order": 30,
                    "keepAlive": True,
                    "activePrefixes": ["/teacher/exemplary"],
                },
            },
            {
                "path": "/teacher/exemplary/:id",
                "name": "TeacherExemplaryDetail",
                "component": "ExemplaryDetail",
                "meta": {"role": "teacher", "title": "优秀作业详情"},
            },
            {
                "path": "/teacher/recycle-bin",
                "name": "TeacherRecycleBin",
                "component": "RecycleBin",
                "meta": {
                    "role": "teacher",
                    "title": "回收站",
                    "icon": "Delete",
                    "nav": True,
                    "order": 40,
                    "activePrefixes": ["/teacher/recycle-bin"],
                },
            },
        ],
    },
}


def get_route_permissions(user: dict):
    """返回该用户角色的路由配置（深拷贝，防止调用方改动全局配置）；未知角色返回 None。"""
    config = ROLE_ROUTE_CONFIG.get(user.get("role"))
    if not config:
        return None
    # 深拷贝让前端/测试拿到的是一次请求的副本，避免误改 ROLE_ROUTE_CONFIG 影响后续用户。
    return {"user": user, **deepcopy(config)}
