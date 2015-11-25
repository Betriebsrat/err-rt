#!/usr/bin/python -tt

# Copyright (c) 2014, John Morrissey <jwm@horde.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#	* Redistributions of source code must retain the above copyright notice,
#	  this list of conditions and the following disclaimer.
#	* Redistributions in binary form must reproduce the above copyright
#	  notice, this list of conditions and the following disclaimer in the
#	  documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import errbot
from errbot import botcmd
import rt
import time


class RTBot(errbot.BotPlugin):
    TICKET_NUM_REGEX = re.compile(
        r'(?:^|\W+)(?:(?:Web)?RT|Ticket)\s*#?(\d{5,6})', re.IGNORECASE)

    tracker = None

    ####################################################################################################################
    # Configuration

    def get_configuration_template(self):
        return {
            "RT_URL": "",
            "RT_USERNAME": "",
            "RT_PASSWORD": "",
        }

    def check_configuration(self, config):
        if type(config) != dict:
            raise Exception("Configuration must be a dict.")

        if "RT_URL" not in config:
            raise Exception("RT_URL must be specified.")
        if "RT_USERNAME" not in config:
            raise Exception("RT_USERNAME must be specified.")
        if "RT_PASSWORD" not in config:
            raise Exception("RT_PASSWORD must be specified.")

        try:
            self.tracker = rt.Rt('%s/REST/1.0/' % config['RT_URL'])
            # FIXME: if False, too(?)
            self.tracker.login(config['RT_USERNAME'], config['RT_PASSWORD'])
        except Exception as e:
            self.tracker = None
            raise Exception("Unable to connect to RT as %s: %s." % (
                config['RT_USERNAME'], str(e),
            ))

        super(RTBot, self).configure(config)

    ####################################################################################################################
    # Helpers

    def login(self):
        if self.tracker:
            return

        self.tracker = rt.Rt('%s/REST/1.0/' % self.config['RT_URL'])
        self.tracker.login(self.config['RT_USERNAME'], self.config['RT_PASSWORD'])

    def ticket_summary(self, num):
        self.login()
        t = self.tracker.get_ticket(num)
        return "%s: %s (%s) in %s, owned by %s (%s/%s)" % (
            num, t.get("Subject", "No subject"),
            t["Status"], t["Queue"], t["Owner"],
            self.config['RT_URL'], num
        )

    def action_report(self, msg, num):
        self.login()
        text = "Chatops: Change from %s in %s at %s. Used Command: %s" % (
        msg.frm, msg.type, time.strftime("%d.%m.%Y %H:%M:%S"), msg.body)
        self.tracker.comment(num, text=text)

    def validate_ticket(self, num):
        self.login()
        if self.tracker.get_ticket(num) is not None:
            return self.tracker.get_ticket(num)
        else:
            return "Ticket not found"

    def validate_user(self, uid):
        self.login()
        if self.tracker.get_user(uid) is not None:
            try:
                self.tracker.get_user(uid)['Name']  # additional check since RT returns incomplete usernames
            except KeyError:
                return "User not found"
            return self.tracker.get_user(uid)
        else:
            return "User not found"

    def callback_message(self, msg):
        matches = self.TICKET_NUM_REGEX.search(msg.body)
        if matches:
            for ticket in matches.groups():
                self.send(msg.frm, self.ticket_summary(ticket),
                          message_type=msg.type)

    ####################################################################################################################
    # Botcommands
    @botcmd
    def rt_search(self, msg, args):
        """"Searches through all ticket queues for given subject. Output limited to 3 items. Usage: !rt search <subject>"""
        if len(args) < 1:
            yield "Usage: !rt search <subject>"
        self.login()
        matches = self.tracker.search(Queue=rt.ALL_QUEUES, order='created', Subject__like=args)
        if matches:
            for ticket in matches[-3:]:
                yield self.ticket_summary(ticket['id'].split('/')[1])
            yield "I found " + str(len(matches)) + " results total."
        else:
            yield "Sorry i did not found any tickets with the subject: " + args

    @botcmd
    def rt_newbodies(self, msg, args):
        """Prints out all tickets with status 'new' and owner 'nobody'. Usage: !rt newbodies"""
        self.login()
        matches = self.tracker.search(Queue=rt.ALL_QUEUES, order='created', raw_query="status='new'+AND+owner='nobody'")
        if matches:
            for ticket in matches:
                yield self.ticket_summary(ticket['id'].split('/')[1])
            yield "I found " + str(len(matches)) + " results total."
        else:
            yield "There aren't any tickets with status 'new' AND owner 'nobody'"


    @botcmd(split_args_with=None)
    def rt_spam(self, msg, args):
        """Closes ticket and sets custom SPAM field to true. Usage : !rt spam <id>"""
        self.login()
        if len(args) != 1:
            return "Usage: !rt spam <id>"

        t_id = args[0]

        if self.validate_ticket(t_id):
            self.tracker.edit_ticket(t_id, Status='resolved', CF_Kontakt='SPAM')
            self.action_report(msg, t_id)
            return "Successfully closed Ticket: #" + t_id
        else:
           return "Something unexpected happened."


    @botcmd(split_args_with=None)
    def rt_give(self, msg, args):
        """Sets a new owner for a ticket. Usage: !rt give <id> <owner>"""
        if len(args) != 2:
            return "Usage: !rt give <id> <owner>"

        t_id = args[0]
        t_owner = args[1]

        if self.validate_ticket(t_id) and self.validate_user(t_owner):
            self.tracker.edit_ticket(t_id, owner=t_owner)
            self.action_report(msg, t_id)
            return "Successfully changed owner of %s to %s." % (t_id, t_owner)
        else:
           return "Something unexpected happened."
