from django.contrib import admin

from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    list_editable = ('group',)
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'slug', 'description')
    search_fields = ('title',)
    list_filter = ('title',)


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
