from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import config
from .sync_service import sync_tick, cleanup_expired_corp_configs


_scheduler = None


def init_scheduler(app=None) -> None:
    """初始化后台调度器，注册占位任务。"""
    global _scheduler
    if _scheduler:
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_tick, "interval", minutes=1, id="sync-tick", replace_existing=True)
    cleanup_interval_seconds = 10 if getattr(config, "DEBUG", False) else 3600
    scheduler.add_job(
        cleanup_expired_corp_configs,
        "interval",
        seconds=cleanup_interval_seconds,
        id="cleanup-corp-config",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler

    # 优雅退出
    atexit.register(lambda: scheduler.shutdown(wait=False))

    if app:
        app.extensions = getattr(app, "extensions", {})
        app.extensions["scheduler"] = scheduler


__all__ = ["init_scheduler"]
