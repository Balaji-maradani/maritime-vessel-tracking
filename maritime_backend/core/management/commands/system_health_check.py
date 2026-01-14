"""
Management command to perform comprehensive system health checks.
Validates database integrity, API connectivity, and system performance.
"""

import json
import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django.conf import settings
from core.models import User, Vessel, Port, Voyage, Event, Notification


class Command(BaseCommand):
    help = '