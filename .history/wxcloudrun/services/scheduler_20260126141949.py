from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from wxcloudrun.services.sync_service import sync_tick


_scheduler = None


def init_scheduler(app=None) -> None:
    """初始化后台调度器，注册占位任务。"""
    global _scheduler
    if _scheduler:
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_tick, "interval", minutes=3, id="sync-tick", replace_existing=True)
    scheduler.start()
    _scheduler = scheduler

    # 优雅退出
    atexit.register(lambda: scheduler.shutdown(wait=False))

    if app:
        app.extensions = getattr(app, "extensions", {})
        app.extensions["scheduler"] = scheduler


__all__ = ["init_scheduler"]
