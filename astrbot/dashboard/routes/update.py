import traceback
from .route import Route, Response, RouteContext
from quart import request
from astrbot.core.core_lifecycle import AstrBotCoreLifecycle
from astrbot.core.updator import AstrBotUpdator
from astrbot.core import logger, pip_installer
from astrbot.core.utils.io import download_dashboard, get_dashboard_version
from astrbot.core.config.default import VERSION

class UpdateRoute(Route):
    def __init__(self, context: RouteContext, astrbot_updator: AstrBotUpdator, core_lifecycle: AstrBotCoreLifecycle) -> None:
        super().__init__(context)
        self.routes = {
            '/update/check': ('GET', self.check_update),
            '/update/do': ('POST', self.update_project),
            '/update/dashboard': ('POST', self.update_dashboard),
            '/update/pip-install': ('POST', self.install_pip_package)
        }
        self.astrbot_updator = astrbot_updator
        self.core_lifecycle = core_lifecycle
        self.register_routes()
    
    async def check_update(self):
        type_ = request.args.get('type', None)
        
        try:
            dv = await get_dashboard_version()
            if type_ == 'dashboard':
                return Response().ok({
                    "has_new_version": dv != f"v{VERSION}",
                    "current_version": dv
                }).__dict__
            else:
                ret = await self.astrbot_updator.check_update(None, None)
                return Response(
                    status="success",
                    message=str(ret) if ret is not None else "已经是最新版本了。",
                    data={
                        "version": f"v{VERSION}",
                        "has_new_version": ret is not None,
                        "dashboard_version": dv,
                        "dashboard_has_new_version": dv != f"v{VERSION}"
                    }
                ).__dict__
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response().error(e.__str__()).__dict__
    
    async def update_project(self):
        data = await request.json
        version = data.get('version', '')
        reboot = data.get('reboot', True)
        if version == "" or version == "latest":
            latest = True
            version = ''
        else:
            latest = False
        try:
            await self.astrbot_updator.update(latest=latest, version=version)
            
            if latest:
                try:
                    await download_dashboard()
                except Exception as e:
                    logger.error(f"下载管理面板文件失败: {e}。")
            
            if reboot:
                # threading.Thread(target=self.astrbot_updator._reboot, args=(2, )).start()
                self.core_lifecycle.restart()
                return Response().ok(None, "更新成功，AstrBot 将在 2 秒内全量重启以应用新的代码。").__dict__
            else:
                return Response().ok(None, "更新成功，AstrBot 将在下次启动时应用新的代码。").__dict__
        except Exception as e:
            logger.error(f"/api/update_project: {traceback.format_exc()}")
            return Response().error(e.__str__()).__dict__
        
    async def update_dashboard(self):
        try:
            try:
                await download_dashboard()
            except Exception as e:
                logger.error(f"下载管理面板文件失败: {e}。")
                return Response().error(f"下载管理面板文件失败: {e}").__dict__
            return Response().ok(None, "更新成功。刷新页面即可应用新版本面板。").__dict__
        except Exception as e:
            logger.error(f"/api/update_dashboard: {traceback.format_exc()}")
            return Response().error(e.__str__()).__dict__
        
    async def install_pip_package(self):
        data = await request.json
        package = data.get('package', '')
        if not package:
            return Response().error("缺少参数 package 或不合法。").__dict__
        try:
            pip_installer.install(package)
            return Response().ok(None, "安装成功。").__dict__
        except Exception as e:
            logger.error(f"/api/update_pip: {traceback.format_exc()}")
            return Response().error(e.__str__()).__dict__