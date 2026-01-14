from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from .models import (
    User, Vessel, Port, Voyage, Event, Notification, 
    VesselSubscription, VesselPosition, VoyageAuditLog
)


class VesselTypeFilter(SimpleListFilter):
    title = 'vessel type'
    parameter_name = 'vessel_type'

    def lookups(self, request, model_admin):
        types = Vessel.objects.values_list('vessel_type', flat=True).distinct()
        return [(t, t) for t in types if t]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(vessel_type=self.value())


class EventTypeFilter(SimpleListFilter):
    title = 'event type'
    parameter_name = 'event_type'

    def lookups(self, request, model_admin):
        return Event.EVENT_TYPE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(event_type=self.value())


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined', 'subscription_count')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    def subscription_count(self, obj):
        return obj.vessel_subscriptions.count()
    subscription_count.short_description = 'Subscriptions'


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    list_display = ('name', 'imo_number', 'mmsi', 'vessel_type', 'flag', 'position_display', 'last_update', 'events_count')
    list_filter = (VesselTypeFilter, 'flag', 'last_update')
    search_fields = ('name', 'imo_number', 'mmsi', 'operator')
    readonly_fields = ('last_update', 'position_link', 'recent_events')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'imo_number', 'mmsi', 'vessel_type', 'flag', 'cargo_type', 'operator')
        }),
        ('Position & Navigation', {
            'fields': ('last_position_lat', 'last_position_lon', 'speed', 'heading', 'position_link')
        }),
        ('System Information', {
            'fields': ('last_update', 'recent_events'),
            'classes': ('collapse',)
        }),
    )
    
    def position_display(self, obj):
        if obj.last_position_lat and obj.last_position_lon:
            return f"{obj.last_position_lat:.4f}, {obj.last_position_lon:.4f}"
        return "No position"
    position_display.short_description = 'Last Position'
    
    def position_link(self, obj):
        if obj.last_position_lat and obj.last_position_lon:
            maps_url = f"https://www.google.com/maps?q={obj.last_position_lat},{obj.last_position_lon}"
            return format_html('<a href="{}" target="_blank">View on Map</a>', maps_url)
        return "No position available"
    position_link.short_description = 'Map Link'
    
    def events_count(self, obj):
        return obj.events.count()
    events_count.short_description = 'Events'
    
    def recent_events(self, obj):
        events = obj.events.order_by('-timestamp')[:5]
        if events:
            event_list = []
            for event in events:
                event_url = reverse('admin:core_event_change', args=[event.id])
                event_list.append(f'<a href="{event_url}">{event.get_event_type_display()} - {event.timestamp.strftime("%Y-%m-%d %H:%M")}</a>')
            return mark_safe('<br>'.join(event_list))
        return "No recent events"
    recent_events.short_description = 'Recent Events'


@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'congestion_display', 'wait_time_display', 'traffic_display', 'last_updated')
    list_filter = ('country', 'last_updated')
    search_fields = ('name', 'location', 'country')
    readonly_fields = ('last_updated', 'congestion_status', 'traffic_summary')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'location', 'country')
        }),
        ('Congestion Analytics', {
            'fields': ('congestion_score', 'avg_wait_time', 'arrivals_count', 'departures_count', 'congestion_status')
        }),
        ('System Information', {
            'fields': ('last_updated', 'traffic_summary'),
            'classes': ('collapse',)
        }),
    )
    
    def congestion_display(self, obj):
        score = obj.congestion_score
        if score >= 8:
            color = 'red'
            status = 'High'
        elif score >= 5:
            color = 'orange'
            status = 'Medium'
        else:
            color = 'green'
            status = 'Low'
        return format_html('<span style="color: {};">{:.1f} ({})</span>', color, score, status)
    congestion_display.short_description = 'Congestion'
    
    def wait_time_display(self, obj):
        return f"{obj.avg_wait_time:.1f} hours"
    wait_time_display.short_description = 'Avg Wait Time'
    
    def traffic_display(self, obj):
        return f"↑{obj.arrivals_count} ↓{obj.departures_count}"
    traffic_display.short_description = 'Traffic'
    
    def congestion_status(self, obj):
        score = obj.congestion_score
        if score >= 8:
            return format_html('<span style="color: red; font-weight: bold;">🔴 HIGH CONGESTION</span>')
        elif score >= 5:
            return format_html('<span style="color: orange; font-weight: bold;">🟡 MODERATE CONGESTION</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">🟢 LOW CONGESTION</span>')
    congestion_status.short_description = 'Status'
    
    def traffic_summary(self, obj):
        net_traffic = obj.arrivals_count - obj.departures_count
        if net_traffic > 0:
            return f"Net inbound: +{net_traffic} vessels"
        elif net_traffic < 0:
            return f"Net outbound: {net_traffic} vessels"
        else:
            return "Balanced traffic"
    traffic_summary.short_description = 'Traffic Summary'


@admin.register(Voyage)
class VoyageAdmin(admin.ModelAdmin):
    list_display = ('vessel_name', 'route_display', 'status', 'departure_time', 'arrival_time', 'duration_display')
    list_filter = ('status', 'departure_time', 'port_from__country', 'port_to__country')
    search_fields = ('vessel__name', 'vessel__imo_number', 'port_from__name', 'port_to__name')
    readonly_fields = ('created_at', 'updated_at', 'duration_display', 'voyage_link')
    
    fieldsets = (
        ('Voyage Information', {
            'fields': ('vessel', 'port_from', 'port_to', 'status')
        }),
        ('Schedule', {
            'fields': ('departure_time', 'arrival_time', 'duration_display')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'voyage_link'),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_name(self, obj):
        return obj.vessel.name
    vessel_name.short_description = 'Vessel'
    
    def route_display(self, obj):
        return f"{obj.port_from.name} → {obj.port_to.name}"
    route_display.short_description = 'Route'
    
    def duration_display(self, obj):
        if obj.arrival_time and obj.departure_time:
            duration = obj.arrival_time - obj.departure_time
            days = duration.days
            hours = duration.seconds // 3600
            return f"{days}d {hours}h"
        return "In progress"
    duration_display.short_description = 'Duration'
    
    def voyage_link(self, obj):
        positions_count = obj.positions.count()
        if positions_count > 0:
            return format_html(
                '<a href="/admin/core/vesselposition/?voyage__id__exact={}">View {} positions</a>',
                obj.id, positions_count
            )
        return "No position data"
    voyage_link.short_description = 'Position Data'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('vessel_name', 'event_type', 'location', 'timestamp', 'notification_count')
    list_filter = (EventTypeFilter, 'timestamp', 'vessel__vessel_type')
    search_fields = ('vessel__name', 'vessel__imo_number', 'location', 'details')
    readonly_fields = ('timestamp', 'related_notifications')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('vessel', 'event_type', 'location', 'details')
        }),
        ('System Information', {
            'fields': ('timestamp', 'related_notifications'),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_name(self, obj):
        return obj.vessel.name
    vessel_name.short_description = 'Vessel'
    
    def notification_count(self, obj):
        return obj.notifications.count()
    notification_count.short_description = 'Notifications'
    
    def related_notifications(self, obj):
        notifications = obj.notifications.all()[:5]
        if notifications:
            notif_list = []
            for notif in notifications:
                notif_url = reverse('admin:core_notification_change', args=[notif.id])
                notif_list.append(f'<a href="{notif_url}">{notif.user.username} - {notif.get_notification_type_display()}</a>')
            return mark_safe('<br>'.join(notif_list))
        return "No notifications"
    related_notifications.short_description = 'Related Notifications'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'vessel_name', 'notification_type', 'is_read', 'timestamp', 'message_preview')
    list_filter = ('notification_type', 'is_read', 'timestamp', 'vessel__vessel_type')
    search_fields = ('user__username', 'vessel__name', 'message')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    actions = ['mark_as_read', 'mark_as_unread']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'vessel', 'event', 'notification_type', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'timestamp')
        }),
    )
    
    def vessel_name(self, obj):
        return obj.vessel.name
    vessel_name.short_description = 'Vessel'
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'


@admin.register(VesselSubscription)
class VesselSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'vessel_name', 'subscription_type', 'notification_settings', 'is_active', 'created_at')
    list_filter = ('subscription_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'vessel__name', 'vessel__imo_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('user', 'vessel', 'subscription_type', 'is_active')
        }),
        ('Notification Preferences', {
            'fields': ('notify_storm_zones', 'notify_piracy_zones', 'notify_congestion', 'notify_position_updates')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_name(self, obj):
        return obj.vessel.name
    vessel_name.short_description = 'Vessel'
    
    def notification_settings(self, obj):
        settings = []
        if obj.notify_storm_zones:
            settings.append('Storm')
        if obj.notify_piracy_zones:
            settings.append('Piracy')
        if obj.notify_congestion:
            settings.append('Congestion')
        if obj.notify_position_updates:
            settings.append('Position')
        return ', '.join(settings) if settings else 'None'
    notification_settings.short_description = 'Notifications'


@admin.register(VesselPosition)
class VesselPositionAdmin(admin.ModelAdmin):
    list_display = ('vessel_name', 'coordinates_display', 'speed', 'heading', 'timestamp', 'source', 'voyage_link')
    list_filter = ('source', 'is_interpolated', 'timestamp', 'vessel__vessel_type')
    search_fields = ('vessel__name', 'vessel__imo_number', 'voyage__id')
    readonly_fields = ('created_at', 'coordinates_display', 'map_link')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Position Information', {
            'fields': ('vessel', 'voyage', 'latitude', 'longitude', 'coordinates_display', 'map_link')
        }),
        ('Navigation Data', {
            'fields': ('speed', 'heading', 'timestamp', 'source', 'accuracy', 'is_interpolated')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_name(self, obj):
        return obj.vessel.name
    vessel_name.short_description = 'Vessel'
    
    def coordinates_display(self, obj):
        return f"{obj.latitude:.6f}, {obj.longitude:.6f}"
    coordinates_display.short_description = 'Coordinates'
    
    def map_link(self, obj):
        maps_url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
        return format_html('<a href="{}" target="_blank">View on Map</a>', maps_url)
    map_link.short_description = 'Map Link'
    
    def voyage_link(self, obj):
        if obj.voyage:
            voyage_url = reverse('admin:core_voyage_change', args=[obj.voyage.id])
            return format_html('<a href="{}">{}</a>', voyage_url, str(obj.voyage))
        return "No voyage"
    voyage_link.short_description = 'Voyage'


@admin.register(VoyageAuditLog)
class VoyageAuditLogAdmin(admin.ModelAdmin):
    list_display = ('vessel_name', 'action', 'user', 'timestamp', 'compliance_category', 'description_preview')
    list_filter = ('action', 'compliance_category', 'timestamp', 'vessel__vessel_type')
    search_fields = ('vessel__name', 'user__username', 'description', 'ip_address')
    readonly_fields = ('timestamp', 'metadata_display')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Information', {
            'fields': ('vessel', 'voyage', 'user', 'action', 'description')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'metadata_display'),
            'classes': ('collapse',)
        }),
        ('Compliance', {
            'fields': ('compliance_category', 'retention_date', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def vessel_name(self, obj):
        return obj.vessel.name
    vessel_name.short_description = 'Vessel'
    
    def description_preview(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'
    
    def metadata_display(self, obj):
        if obj.metadata:
            import json
            return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
        return "No metadata"
    metadata_display.short_description = 'Metadata'


# Customize admin site header and title
admin.site.site_header = "Maritime Analytics Administration"
admin.site.site_title = "Maritime Analytics Admin"
admin.site.index_title = "Welcome to Maritime Analytics Administration"
