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
import rt

class RTBot(errbot.BotPlugin):
	min_err_version = "2.0.0"
	max_err_version = "2.0.0"

	TICKET_NUM_REGEX = re.compile(
		r'(?:^|\W+)(?:(?:Web)?RT|Ticket)\s*#?(\d{5,6})', re.IGNORECASE)

	tracker = None

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

	def login(self):
		if self.tracker:
			return

		self.tracker = rt.Rt('%s/REST/1.0/' % self.config['RT_URL'])
		self.tracker.login(self.config['RT_USERNAME'], self.config['RT_PASSWORD'])

	def ticket_summary(self, num):
		self.login()
		t = self.tracker.get_ticket(num)

		return "RT %s: %s (%s) in %s, owned by %s (%s/%s)" % (
			num, t.get("Subject", "No subject"),
			t["Status"], t["Queue"], t["Owner"],
			self.config['RT_URL'], num,
		)

	def callback_message(self, conn, msg):
		matches = self.TICKET_NUM_REGEX.search(msg.getBody())
		if matches:
			for ticket in matches.groups():
				self.send(msg.getFrom(), self.ticket_summary(ticket),
					message_type=msg.getType())
