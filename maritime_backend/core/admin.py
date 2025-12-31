from django.contrib import admin
from .models import User, Vessel, Port, Voyage, Event, Notification

admin.site.register(User)
admin.site.register(Vessel)
admin.site.register(Port)
admin.site.register(Voyage)
admin.site.register(Event)
admin.site.register(Notification)
