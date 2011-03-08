#
# Copyright (c) 2008-2011 Brad Taylor <brad@getcoded.net>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import imaplib
import pprint
import email
import re

from django.utils.html import escape

from berserk2 import settings
from berserk2.timeline.models import Actor, Event
from berserk2.sprints.models import Task, BugTracker

class FogBugzEmailSource():
    def __init__(self):
        self.name = 'FogBugz'

    @staticmethod
    def enabled():
        """
        Returns true if the source is configured properly and should be run.
        """
        return settings.FB_EMAIL_SOURCE_HOST != '' \
               and settings.FB_EMAIL_SOURCE_USER != '' \
               and settings.FB_EMAIL_SOURCE_USER != ''

    def run(self):
        """
        Runs a single iteration of the source, in this case, polling for the
        first set of unread messages.
        """
        c = imaplib.IMAP4_SSL(settings.FB_EMAIL_SOURCE_HOST)
        c.login(settings.FB_EMAIL_SOURCE_USER, settings.FB_EMAIL_SOURCE_PASSWORD)
        try:
            c.select('INBOX')

            typ, [msg_ids] = c.search(None, 'UNSEEN')
            if msg_ids == '':
                return

            for i in msg_ids.split(' '):
                typ, msg_data = c.fetch(i, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_string(response_part[1])
                        body = msg.get_payload(decode=True)
                        if not body:
                            continue
                        tokens = self._tokenize_body(body)
                        self._parse_body(tokens)
        finally:
            try:
                c.close()
            except:
                pass
            c.logout()

    def _tokenize_body(self, body):
        lines = body.split('\r\n')

        case_id = 0
        changes = []
        begin_changes_block = False

        comment = []
        begin_comment_block = False

        i = 0
        while i < len(lines):
            l = lines[i].strip()
            n = lines[i+1].strip() if i + 1 < len(lines) else None
            m = lines[i+2].strip() if i + 2 < len(lines) else None

            # Look for the end of email marker
            if l == '' and n == '':
                if m and m.startswith('You are subscribed'):
                    break
                elif m and m.startswith('If you do not want to receive'):
                    break

            if l.startswith('URL:'):
                i += 1 # Skip over the following blank line
                begin_comment_block = True
                begin_changes_block = False
            elif l.startswith('Last message:'):
                begin_comment_block = True
                begin_changes_block = False
            elif l.startswith('Changes:'):
                begin_changes_block = True
                begin_comment_block = False
            elif begin_comment_block:
                comment.append(l)
            elif begin_changes_block:
                changes.append(l)

            if l.startswith('Case ID:'):
                foo, bar, case_id = l.split()
                case_id = int(case_id)

            i += 1

        return {'subject': lines[0],
                'case_id': case_id,
                'changes': changes,
                'comment': comment}

    def _parse_body(self, tokens):
        message = ''
        protagonist = ''
        deuteragonist = ''

        subject = tokens['subject']
        case_id = int(tokens['case_id'])
        changes = tokens['changes']
        comment = tokens['comment']

        m = re.search('by (\w+ \w+)', subject)
        if m:
            protagonist = m.group(1)

        # Subject matching
        if subject.startswith('A new case'):
            self._add_event(case_id, protagonist, None,
                            '{{ protagonist }} opened a new case {{ task_link }}.', comment)
        elif subject.startswith('A FogBugz case was assigned to'):
            m = re.search('A FogBugz case was assigned to (.*) by', subject)
            deuteragonist = m.group(1)
            print 'protagonist: $%s$' % protagonist
            print 'deuteragonist: $%s$' % deuteragonist
            if protagonist == deuteragonist:
                print 'equal'
                self._add_event(case_id, protagonist, None,
                               '{{ protagonist }} assigned case {{ task_link }} to {{ proto_self }}.', comment)
            else:
                print 'not equal'
                self._add_event(case_id, protagonist, deuteragonist,
                               '{{ protagonist }} assigned case {{ task_link }} to {{ deuteragonist }}.', comment)
        elif subject.startswith('A FogBugz case was closed by'):
            self._add_event(case_id, protagonist, None,
                           '{{ protagonist }} closed {{ task_link }}.', comment)
        elif len(changes) == 0:
            self._add_event(case_id, protagonist, None,
                           '{{ protagonist }} commented on {{ task_link }}.', comment)
        else:
            # Examine changes.  Each change will result in an update.
            for change in changes:
                m = re.match("Estimate set to '(?P<hours>\d+.?\d*) hours'", change)
                if m:
                    hours = float(m.group('hours'))
                    plural = 'hour' if hours == 1 else 'hours'
                    self._add_event(case_id, protagonist, None,
                                    "{{ protagonist }} estimates {{ task_link }} will require %s %s to complete." % (hours, plural),
                                    comment)
                    continue

                m = re.match('(?P<type>.+) changed from \'(?P<before>.*)\' to \'(?P<after>.*)\'.?', change)
                if not m:
                    continue

                type = m.group('type').lower()
                before = m.group('before')
                after = m.group('after')

                if type == 'milestone':
                    self._add_event(case_id, protagonist, None,
                                    "{{ protagonist }} moved {{ task_link }} to the '%s' milestone." % after,
                                    comment)
                elif type == 'title':
                    self._add_event(case_id, protagonist, None,
                                    "{{ protagonist }} changed the title of {{ task_link }} to '%s'." % escape(after),
                                    comment)
                elif type == 'non-timesheet elapsed time':
                    hours = float(after.split(' ', 1)[0])
                    plural = 'hour has' if hours == 1 else 'hours have'
                    self._add_event(case_id, protagonist, None,
                                    "{{ protagonist }} reports that %s %s been spent on {{ task_link }}." % (hours, plural),
                                    comment)
                elif type == 'status':
                    if before.startswith('Resolved') and after == 'Active':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} reopened {{ task_link }}.", comment)
                    elif after == 'Resolved (Fixed)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as fixed.", comment)
                    elif after == 'Resolved (Not Reproducible)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as not reproducible.", comment)
                    elif after == 'Resolved (Duplicate)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as duplicate.", comment)
                    elif after == 'Resolved (Postpooned)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as postponed.", comment)
                    elif after == 'Resolved (By Design)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as by design.", comment)
                    elif after == 'Resolved (Won\'t Fix)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as won't fix.", comment)
                    elif after == 'Resolved (Implemented)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as implemented.", comment)
                    elif after == 'Resolved (Completed)':
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked {{ task_link }} as completed.", comment)
                    else:
                        self._add_event(case_id, protagonist, None,
                                        "{{ protagonist }} marked the status of {{ task_link }} as %s." % after,
                                        comment)
                else:
                    self._add_event(case_id, protagonist, None,
                                    "{{ protagonist }} changed the %s of {{ task_link }} from %s to %s." % \
                                    (type, before, after), comment)


    def _add_event(self, case_id, protagonist, deuteragonist, message, comment):
        task, created = Task.objects.get_or_create(remote_tracker_id=case_id,
                                                   bug_tracker=BugTracker.objects.all()[0])

        # We always want to fetch a new snapshot as this event has probably
        # caused an update.
        snap = task.snapshot()

        if protagonist:
            protagonist, created = Actor.objects.get_or_create_by_full_name(protagonist)

        if deuteragonist:
            deuteragonist, created = Actor.objects.get_or_create_by_full_name(deuteragonist)

        comments = '\n'.join(comment)

        return Event.objects.create(
            source=self.name, protagonist=protagonist, deuteragonist=deuteragonist,
            message=message, comment=comments, task=task
        )
