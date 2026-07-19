"""Azure Functions (Python v2 model) timer trigger.

Runs every 5 minutes, every day -- the *actual* Mon-Fri 6am-6pm
America/Phoenix restriction is enforced in code by
``realty_agent.scheduler.is_within_operating_window`` (see
``realty_agent.main.run``) rather than in the CRON expression, so the
operating days/hours stay configurable via ``config/settings.yaml``
without redeploying the Function.
"""

import azure.functions as func

from realty_agent.main import run

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 */5 * * * *",  # every 5 minutes, every day (window checked in run())
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def listing_sync_timer(timer: func.TimerRequest) -> None:
    run()
