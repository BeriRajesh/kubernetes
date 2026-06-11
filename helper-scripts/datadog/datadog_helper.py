import datadog
import json
import os
import sys

os.chdir(os.path.realpath(os.path.dirname(__file__)))
sys.path.append('../')
import lib.helper_functions as hf


class DatadogHelper:

    datadog = None

    def __init__(self):
        # reading datadog keys from environment
        options = {
            'api_key': os.environ['DD_API_KEY'],
            'app_key': os.environ['DD_APP_KEY']
        }
        # strip() necessary in some systems that return the variable with a "\r"
        options = {k: v.strip() for k, v in options.items()}

        datadog.initialize(**options)
        self.datadog = datadog

    def get_screenboard(self, id, **kwargs):
        board = self.datadog.api.Screenboard.get(id, **kwargs)
        if "errors" not in board.keys():
            return board

        board = self.datadog.api.Timeboard.get(id, **kwargs)
        if "errors" not in board.keys():
            return board

        sys.exit("id `{}` Not found as Screenboard or dashboard ".format(id))

    def create_screenboard(self, screenboard):
        return self.datadog.api.Screenboard.create(screenboard)

    def update_screenboard(self, screenboard_id, screenboard):
        """
        Updates or creates a screenboard

        Args:
            screenboard_id (int): the id of the screenboard to update. If not provided it will try to look in
            screenboard, and
                if not try to create the screenboard
            screenboard (dict): dictionary specifying the screenboard arguments

        Returns:
            object response from datadog API

        """

        if screenboard_id is None and 'id' not in screenboard:
            if "board_title" in screenboard:
                hf.debug('creating screenboard {}'.format(screenboard['board_title']))
                return self.datadog.api.Screenboard.create(
                    board_title=screenboard['board_title'],
                    widgets=screenboard['widgets'],
                    template_variables=screenboard['template_variables'],
                    width=screenboard['width']
                )

        screenboard_id = screenboard_id or screenboard['id']
        hf.debug('updating')
        return self.datadog.api.Screenboard.update(
            screenboard_id,
            board_title=screenboard['board_title'],
            widgets=screenboard['widgets'],
            template_variables=screenboard['template_variables'],
            width=screenboard['width']
        )

    def update_timeboard(self, screenboard_id, screenboard):
        """
        Updates or creates a timeboard

        Args:
            screenboard_id (int): the id of the screenboard to update. If not provided it will try to look in
            screenboard, and
                if not try to create the screenboard
            screenboard (dict): dictionary specifying the screenboard arguments

        Returns:
            object response from datadog API

        """

        if screenboard_id is None and 'id' not in screenboard["dash"]:
            hf.debug('creating screenboard {}'.format(screenboard["dash"]['title']))
            return self.datadog.api.Timeboard.create(
                title=screenboard['dash']['title'],
                description=screenboard['dash']['description'],
                graphs=screenboard['dash']['graphs'],
                template_variables=screenboard['dash']['template_variables'] if "template_variables" in screenboard['dash'] else [],
            )

        screenboard_id = screenboard_id or screenboard["dash"]['id']
        hf.debug('updating')
        return self.datadog.api.Screenboard.update(
            screenboard_id,
            title=screenboard['dash']['title'],
            description=screenboard['dash']['description'],
            graphs=screenboard['dash']['graphs'],
            template_variables=screenboard['dash']['template_variables'] if "template_variables" in screenboard['dash'] else [],
        )



