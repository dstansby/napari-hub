import logging
from datetime import datetime

from activity.install_activity_model import InstallActivityType
import activity.install_activity_model as install_model
from activity.github_activity_model import GitHubActivityType
import activity.github_activity_model as github_model
import activity.snowflake_adapter as snowflake
from utils.utils import ParameterStoreAdapter
import nhcommons

LOGGER = logging.getLogger()


def _fetch_install_data_and_write_to_dynamo(
    data: dict[str, datetime], install_activity_type: InstallActivityType
) -> None:
    plugin_install_data = snowflake.get_plugins_install_count_since_timestamp(
        data, install_activity_type
    )
    install_model.transform_and_write_to_dynamo(
        plugin_install_data, install_activity_type
    )


def _fetch_github_data_and_write_to_dynamo(
    data: dict[str, datetime], github_activity_type: GitHubActivityType
) -> None:
    plugin_commit_data = snowflake.get_plugins_commit_count_since_timestamp(
        data, github_activity_type
    )
    github_model.transform_and_write_to_dynamo(
        plugin_commit_data, github_activity_type
    )


def _update_install_activity(start_time: int, end_time: int) -> None:
    updated_plugins = snowflake.get_plugins_with_installs_in_window(
        start_time, end_time
    )
    count = len(updated_plugins)
    LOGGER.info(f"Plugins with new install activity count={count}")
    if count == 0:
        return

    _fetch_install_data_and_write_to_dynamo(updated_plugins, InstallActivityType.DAY)
    _fetch_install_data_and_write_to_dynamo(updated_plugins, InstallActivityType.MONTH)
    _fetch_install_data_and_write_to_dynamo(updated_plugins, InstallActivityType.TOTAL)


def _update_github_activity(start_time: int, end_time: int) -> None:
    updated_plugins = snowflake.get_plugins_with_commits_in_window(
        start_time, end_time
    )
    count = len(updated_plugins)
    LOGGER.info(f"Plugins with new github activity count={count}")
    if count == 0:
        return
    _fetch_github_data_and_write_to_dynamo(updated_plugins, GitHubActivityType.LATEST)
    _fetch_github_data_and_write_to_dynamo(updated_plugins, GitHubActivityType.MONTH)
    _fetch_github_data_and_write_to_dynamo(updated_plugins, GitHubActivityType.TOTAL)


def update_activity() -> None:
    parameter_store = ParameterStoreAdapter()
    last_updated_timestamp = parameter_store.get_last_updated_timestamp()
    current_timestamp = nhcommons.utils.get_current_timestamp()
    _update_install_activity(last_updated_timestamp, current_timestamp)
    _update_github_activity(last_updated_timestamp, current_timestamp)
    parameter_store.set_last_updated_timestamp(current_timestamp)
