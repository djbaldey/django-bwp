# coding: utf-8
"""
Management utility for delete all sessions.
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session


class Command(BaseCommand):

    help = 'Used to runs process for delete all sessions.'

    def handle(self, *args, **options):
        Session.objects.all().delete()
