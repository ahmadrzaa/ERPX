"""
erpx/generic/views.py
"""

import json
from typing import Any
from urllib.parse import parse_qs

from bs4 import BeautifulSoup
from django import forms
from django.contrib import messages
from django.core.cache import cache as CACHE
from django.core.paginator import Page
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import render
from django.urls import resolve, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _trans
from django.views.generic import DetailView, FormView, ListView, TemplateView

from base.methods import closest_numbers, get_key_instances
from erpx.filters import FilterSet
from erpx.group_by import group_by_queryset
from erpx.erpx_middlewares import _thread_locals
from erpx_views import models
from erpx_views.cbv_methods import (
    get_short_uuid,
    hx_request_required,
    paginator_qry,
    sortby,
    structured,
    update_initial_cache,
    update_saved_filter_cache,
)
from erpx_views.forms import DynamicBulkUpdateForm, ToggleColumnForm
from erpx_views.templatetags.generic_template_filters import getattribute


@method_decorator(hx_request_required, name="dispatch")
class erpxListView(ListView):
    """
    erpxListView
    """

    filter_class: FilterSet = None

    view_id: str = """"""

    export_file_name: str = None

    template_name: str = "generic/erpx_list_table.html"
    context_object_name = "queryset"
    # column = [("Verbose Name","field_name","avatar_mapping")], opt: avatar_mapping
    columns: list = []
    search_url: str = ""
    bulk_select_option: bool = True

    action_method: str = """"""
    """
    eg:
    def accessibility(
        request, instance: object = None, user_perms: PermWrapper = [], *args, **kwargs
    )->bool:
        # True if accessible to the action else False
        return True

    actions = [
        {
            "action": "Edit",
            "accessibility": "path_to_your.accessibility", # path to your accessibility method
            "attrs": '''{instance_attributes_called_like_this}''',
        },
        etc..
    ]
    """
    actions: list = []

    option_method: str = ""
    options: list = []
    row_attrs: str = """"""
    row_status_class: str = """"""
    row_status_indications: list = []

    sortby_key: str = "sortby"
    sortby_mapping: list = []

    selected_instances_key_id: str = "selectedInstances"

    show_filter_tags: bool = True
    show_toggle_form: bool = True
    filter_keys_to_remove: list = []

    records_per_page: int = 50
    export_fields: list = []
    verbose_name: str = ""

    bulk_update_fields: list = []
    bulk_template: str = "generic/bulk_form.html"

    header_attrs: dict = {}

    def __init__(self, **kwargs: Any) -> None:
        if not self.view_id:
            self.view_id = get_short_uuid(4)
        super().__init__(**kwargs)

        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxListView)

        # hidden columns configuration
        existing_instance = models.ToggleColumn.objects.filter(
            user_id=request.user, path=request.path_info
        ).first()

        hidden_fields = (
            [] if not existing_instance else existing_instance.excluded_columns
        )

        self.visible_column = self.columns.copy()

        self.toggle_form = ToggleColumnForm(self.columns, hidden_fields)
        for column in self.columns:
            if column[1] in hidden_fields:
                self.visible_column.remove(column)

    def bulk_update_accessibility(self) -> bool:
        """
        Accessibility method for bulk update
        """
        return self.request.user.has_perm(
            f"{self.model._meta.app_label}.change_{self.model.__name__.lower()}"
        )

    def serve_bulk_form(self, request: HttpRequest) -> HttpResponse:
        """
        Bulk form serve method
        """

        if not self.bulk_update_accessibility():
            return HttpResponse("You dont have permission")
        form = self.get_bulk_form()
        form.verbose_name = (
            form.verbose_name
            + f" ({len((eval(request.GET.get('instance_ids','[]'))))} {_trans('Records')})"
        )
        return render(
            request,
            self.bulk_template,
            {"form": form, "post_bulk_path": self.post_bulk_path},
        )

    def handle_bulk_submission(self, request: HttpRequest) -> HttpRequest:
        """
        This method to handle bulk update form submission
        """
        if not self.bulk_update_accessibility():
            return HttpResponse("You dont have permission")

        instance_ids = request.GET.get("instance_ids", "[]")
        instance_ids = eval(instance_ids)
        form = DynamicBulkUpdateForm(
            request.POST,
            request.FILES,
            root_model=self.model,
            bulk_update_fields=self.bulk_update_fields,
            ids=instance_ids,
        )
        if instance_ids and form.is_valid():
            form.save()

            script_id = get_short_uuid(length=3, prefix="bulk")
            return HttpResponse(
                f"""
                <script id="{script_id}">
                    $("#{script_id}").closest(".oh-modal--show").removeClass("oh-modal--show");
                    $(".reload-record").click()
                    $("#reloadMessagesButton").click()
                </script>
                """
            )
        if not instance_ids:
            messages.info(request, _trans("No records selected"))
        return render(
            request,
            self.bulk_template,
            {"form": form, "post_bulk_path": self.post_bulk_path},
        )

    def get_bulk_form(self):
        """
        Bulk from generating method
        """
        # Bulk update feature
        return DynamicBulkUpdateForm(
            root_model=self.model, bulk_update_fields=self.bulk_update_fields
        )

    def get_queryset(self):
        if not self.queryset:
            self.queryset = super().get_queryset()
            self._saved_filters = QueryDict("", mutable=True)
            if self.filter_class:
                query_dict = self.request.GET
                if "filter_applied" in query_dict.keys():
                    update_saved_filter_cache(self.request, CACHE)
                elif CACHE.get(
                    str(self.request.session.session_key) + self.request.path + "cbv"
                ):
                    query_dict = CACHE.get(
                        str(self.request.session.session_key)
                        + self.request.path
                        + "cbv"
                    )["query_dict"]

                default_filter = models.SavedFilter.objects.filter(
                    path=self.request.path,
                    created_by=self.request.user,
                    is_default=True,
                ).first()
                if not bool(query_dict) and default_filter:
                    data = eval(default_filter.filter)
                    query_dict = QueryDict("", mutable=True)
                    for key, value in data.items():
                        query_dict[key] = value

                    query_dict._mutable = False
                self._saved_filters = query_dict
                self.request.exclude_filter_form = True
                self.queryset = self.filter_class(
                    data=query_dict, queryset=self.queryset, request=self.request
                ).qs
        return self.queryset

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context["view_id"] = self.view_id
        context["columns"] = self.visible_column
        context["hidden_columns"] = list(set(self.columns) - set(self.visible_column))
        context["toggle_form"] = self.toggle_form
        context["show_toggle_form"] = self.show_toggle_form
        context["search_url"] = self.search_url

        context["action_method"] = self.action_method
        context["actions"] = self.actions

        context["option_method"] = self.option_method
        context["options"] = self.options
        context["row_attrs"] = self.row_attrs

        context["header_attrs"] = self.header_attrs

        context["show_filter_tags"] = self.show_filter_tags
        context["bulk_select_option"] = self.bulk_select_option
        context["row_status_class"] = self.row_status_class
        context["sortby_key"] = self.sortby_key
        context["sortby_mapping"] = self.sortby_mapping
        context["selected_instances_key_id"] = self.selected_instances_key_id
        context["row_status_indications"] = self.row_status_indications
        context["saved_filters"] = self._saved_filters
        if not self.verbose_name:
            self.verbose_name = self.model.__class__
        context["model_name"] = self.verbose_name
        context["export_fields"] = self.export_fields
        referrer = self.request.GET.get("referrer", "")
        if referrer:
            # Remove the protocol and domain part
            referrer = "/" + "/".join(referrer.split("/")[3:])
        context["stored_filters"] = (
            models.SavedFilter.objects.filter(
                path=self.request.path, created_by=self.request.user
            )
            | models.SavedFilter.objects.filter(
                referrer=referrer, created_by=self.request.user
            )
        ).distinct()

        context["select_all_ids"] = self.select_all
        if self._saved_filters.get("field"):
            active_group = models.ActiveGroup.objects.filter(
                created_by=self.request.user,
                path=self.request.path,
                group_by_field=self._saved_filters["field"],
            ).first()
            if active_group:
                context["active_target"] = active_group.group_target

        queryset = self.get_queryset()

        if self.show_filter_tags:
            data_dict = parse_qs(self._saved_filters.urlencode())
            data_dict = get_key_instances(self.model, data_dict)
            keys_to_remove = [
                key
                for key, value in data_dict.items()
                if value[0] in ["unknown", "on"] + self.filter_keys_to_remove
            ]

            for key in keys_to_remove + ["referrer"]:
                if key in data_dict.keys():
                    data_dict.pop(key)
            context["filter_dict"] = data_dict

        request = self.request
        ordered_ids = list(queryset.values_list("id", flat=True))
        is_first_sort = False
        query_dict = self.request.GET
        if (
            not request.GET.get(self.sortby_key)
            and not self._saved_filters.get(self.sortby_key)
        ) or (
            not request.GET.get(self.sortby_key)
            and self._saved_filters.get(self.sortby_key)
        ):
            is_first_sort = True
            query_dict = self._saved_filters

        if query_dict.get(self.sortby_key):
            queryset = sortby(
                query_dict, queryset, self.sortby_key, is_first_sort=is_first_sort
            )

            ordered_ids = [instance.id for instance in queryset]
        ordered_ids = []
        if not self._saved_filters.get("field"):
            for instance in queryset:
                instance.ordered_ids = ordered_ids
                ordered_ids.append(instance.pk)

        context["queryset"] = paginator_qry(
            queryset, self._saved_filters.get("page"), self.records_per_page
        )

        if request and self._saved_filters.get("field"):
            field = self._saved_filters.get("field")
            self.template_name = "generic/group_by_table.html"
            if isinstance(queryset, Page):
                queryset = self.filter_class(
                    request.GET, queryset=queryset.object_list.model.objects.all()
                ).qs
            groups = group_by_queryset(
                queryset, field, self._saved_filters.get("page"), "page"
            )
            context["groups"] = paginator_qry(
                groups, self._saved_filters.get("page"), 10
            )

            for group in context["groups"]:
                for instance in group["list"]:
                    instance.ordered_ids = ordered_ids
                    ordered_ids.append(instance.pk)
        CACHE.get(self.request.session.session_key + "cbv")[erpxListView] = context
        from erpx.urls import path, urlpatterns

        self.export_path = f"export-list-view-{get_short_uuid(4)}/"

        urlpatterns.append(path(self.export_path, self.export_data))
        context["export_path"] = self.export_path

        if self.bulk_update_fields and self.bulk_update_accessibility():
            get_bulk_path = (
                f"get-bulk-update-{self.view_id}-{self.request.session.session_key}/"
            )
            post_bulk_path = (
                f"post-bulk-update-{self.view_id}-{self.request.session.session_key}/"
            )
            self.post_bulk_path = post_bulk_path
            urlpatterns.append(
                path(
                    get_bulk_path,
                    self.serve_bulk_form,
                )
            )
            urlpatterns.append(
                path(
                    post_bulk_path,
                    self.handle_bulk_submission,
                )
            )
            context["bulk_update_fields"] = self.bulk_update_fields
            context["bulk_path"] = get_bulk_path

        return context

    def select_all(self, *args, **kwargs):
        """
        Select all method
        """
        return json.dumps(list(self.get_queryset().values_list("id", flat=True)))

    def export_data(self, *args, **kwargs):
        """
        Export list view visible columns
        """
        from import_export import fields, resources

        request = getattr(_thread_locals, "request", None)
        ids = eval(request.GET["ids"])
        _columns = eval(request.GET["columns"])
        queryset = self.model.objects.filter(id__in=ids)

        _model = self.model

        class erpxListViewResorce(resources.ModelResource):
            """
            Instant Resource class
            """

            id = fields.Field(column_name="ID")

            class Meta:
                """
                Meta class for additional option
                """

                model = _model
                fields = []

            def dehydrate_id(self, instance):
                """
                Dehydrate method for id field
                """
                return instance.pk

            for field_tuple in _columns:
                dynamic_fn_str = f"def dehydrate_{field_tuple[1]}(self, instance):return self.remove_extra_spaces(getattribute(instance, '{field_tuple[1]}'))"
                exec(dynamic_fn_str)
                dynamic_fn = locals()[f"dehydrate_{field_tuple[1]}"]
                locals()[field_tuple[1]] = fields.Field(column_name=field_tuple[0])

            def remove_extra_spaces(self, text):
                """
                Remove blank space but keep line breaks and add new lines for <li> tags.
                """
                soup = BeautifulSoup(str(text), "html.parser")
                for li in soup.find_all("li"):
                    li.insert_before("\n")
                    li.unwrap()
                text = soup.get_text()
                lines = text.splitlines()
                non_blank_lines = [line.strip() for line in lines if line.strip()]
                cleaned_text = "\n".join(non_blank_lines)
                return cleaned_text

        book_resource = erpxListViewResorce()

        # Export the data using the resource
        dataset = book_resource.export(queryset)

        excel_data = dataset.export("xls")

        # Set the response headers
        file_name = self.export_file_name
        if not file_name:
            file_name = "quick_export"
        response = HttpResponse(excel_data, content_type="application/vnd.ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{file_name}.xls"'
        return response


class erpxSectionView(TemplateView):
    """
    erpx Template View
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxListView)

    nav_url: str = ""
    view_url: str = ""

    # view container id is used to wrap the component view with th id
    view_container_id: str = ""

    script_static_paths: list = []
    style_static_paths: list = []

    template_name = "generic/erpx_section.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["nav_url"] = self.nav_url
        context["view_url"] = self.view_url
        context["view_container_id"] = self.view_container_id
        context["script_static_paths"] = self.script_static_paths
        context["style_static_paths"] = self.style_static_paths
        return context


@method_decorator(hx_request_required, name="dispatch")
class erpxDetailedView(DetailView):
    """
    HorillDetailedView
    """

    title = "Detailed View"
    template_name = "generic/erpx_detailed_view.html"
    header: dict = {"title": "erpx", "subtitle": "erpx Detailed View"}
    body: list = []

    action_method: list = []
    actions: list = []
    cols: dict = {}

    ids_key: str = "instance_ids"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxDetailedView)

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        instance_ids = eval(str(self.request.GET.get(self.ids_key)))

        pk = context["object"].pk
        if instance_ids:
            context["object"].ordered_ids = instance_ids
        context["instance"] = context["object"]

        url = resolve(self.request.path)
        key = list(url.kwargs.keys())[0]

        url_name = url.url_name

        previous_id, next_id = closest_numbers(instance_ids, pk)

        next_url = reverse(url_name, kwargs={key: next_id})
        previous_url = reverse(url_name, kwargs={key: previous_id})
        if instance_ids:
            context["instance_ids"] = str(instance_ids)
            context["ids_key"] = self.ids_key

            context["next_url"] = next_url
            context["previous_url"] = previous_url

        context["title"] = self.title
        context["header"] = self.header
        context["body"] = self.body
        context["actions"] = self.actions
        context["action_method"] = self.action_method
        context["cols"] = self.cols

        CACHE.get(self.request.session.session_key + "cbv")[
            erpxDetailedView
        ] = context

        return context


@method_decorator(hx_request_required, name="dispatch")
class erpxTabView(TemplateView):
    """
    erpxTabView
    """

    view_id: str = get_short_uuid(3, "htv")
    template_name = "generic/erpx_tabs.html"

    tabs: list = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxTabView)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user:
            active_tab = models.ActiveTab.objects.filter(
                created_by=self.request.user, path=self.request.path
            ).first()
            if active_tab:
                context["active_target"] = active_tab.tab_target
        context["tabs"] = self.tabs
        context["view_id"] = self.view_id

        CACHE.get(self.request.session.session_key + "cbv")[erpxTabView] = context

        return context


@method_decorator(hx_request_required, name="dispatch")
class erpxCardView(ListView):
    """
    erpxCardView
    """

    filter_class: FilterSet = None

    view_id: str = get_short_uuid(4, prefix="hcv")

    template_name = "generic/erpx_card.html"
    context_object_name = "queryset"

    search_url: str = ""

    details: dict = {}
    """
    eg:
    def accessibility(
        request, instance: object = None, user_perms: PermWrapper = [], *args, **kwargs
    )->bool:
        # True if accessible to the action else False
        return True

    actions = [
        {
            "action": "Edit",
            "accessibility": "path_to_your.accessibility", # path to your accessibility method
            "attrs": '''{instance_attributes_called_like_this}''',
        },
        etc..
    ]
    """
    actions: list = []

    card_attrs: str = """"""

    show_filter_tags: bool = True
    filter_keys_to_remove: list = []

    records_per_page: int = 50
    card_status_class: str = """"""
    card_status_indications: list = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxCardView)
        self._saved_filters = QueryDict()

    def get_queryset(self):
        if not self.queryset:
            queryset = super().get_queryset()
            if self.filter_class:
                query_dict = self.request.GET
                if "filter_applied" in query_dict.keys():
                    update_saved_filter_cache(self.request, CACHE)
                elif CACHE.get(
                    str(self.request.session.session_key) + self.request.path + "cbv"
                ):
                    query_dict = CACHE.get(
                        str(self.request.session.session_key)
                        + self.request.path
                        + "cbv"
                    )["query_dict"]

                self._saved_filters = query_dict
                self.request.exclude_filter_form = True
                self.queryset = self.filter_class(
                    query_dict, queryset, request=self.request
                ).qs
                default_filter = models.SavedFilter.objects.filter(
                    path=self.request.path,
                    created_by=self.request.user,
                    is_default=True,
                ).first()
                if not bool(query_dict) and default_filter:
                    data = eval(default_filter.filter)
                    query_dict = QueryDict("", mutable=True)
                    for key, value in data.items():
                        query_dict[key] = value

                    query_dict._mutable = False

        return self.queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()

        context["view_id"] = self.view_id
        context["search_url"] = self.search_url
        context["card_attrs"] = self.card_attrs
        context["actions"] = self.actions
        context["details"] = self.details
        context["show_filter_tags"] = self.show_filter_tags
        context["card_status_class"] = self.card_status_class
        context["card_status_indications"] = self.card_status_indications

        if self.show_filter_tags:
            data_dict = parse_qs(self._saved_filters.urlencode())
            data_dict = get_key_instances(self.model, data_dict)
            keys_to_remove = [
                key
                for key, value in data_dict.items()
                if value[0] in ["unknown", "on"] + self.filter_keys_to_remove
            ]

            for key in keys_to_remove + ["referrer"]:
                if key in data_dict.keys():
                    data_dict.pop(key)
            context["filter_dict"] = data_dict

        ordered_ids = list(queryset.values_list("id", flat=True))
        if not self._saved_filters.get("field"):
            for instance in queryset:
                instance.ordered_ids = ordered_ids
                ordered_ids.append(instance.pk)

        CACHE.get(self.request.session.session_key + "cbv")[erpxCardView] = context
        referrer = self.request.GET.get("referrer", "")
        if referrer:
            # Remove the protocol and domain part
            referrer = "/" + "/".join(referrer.split("/")[3:])
        context["stored_filters"] = (
            models.SavedFilter.objects.filter(
                path=self.request.path, created_by=self.request.user
            )
            | models.SavedFilter.objects.filter(
                referrer=referrer, created_by=self.request.user
            )
        ).distinct()
        context["queryset"] = paginator_qry(
            queryset, self.request.GET.get("page"), self.records_per_page
        )
        return context


@method_decorator(hx_request_required, name="dispatch")
class ReloadMessages(TemplateView):
    """
    Reload messages
    """

    template_name = "generic/messages.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def save(self: forms.ModelForm, commit=True, *args, **kwargs):
    """
    This method is used to super save the form using custom logic
    """
    request = getattr(_thread_locals, "request", None)

    dynamic_field = request.GET["dynamic_field"]
    response = None
    if commit:
        response = super(type(self), self).save(*args, **kwargs)
        new_isntance_pk = self.instance.pk
        CACHE.set(
            request.session.session_key + "cbv" + dynamic_field,
            {
                "dynamic_field": dynamic_field,
                "value": new_isntance_pk,
                "model": self._meta.model,
            },
        )
    return response


@method_decorator(hx_request_required, name="dispatch")
class erpxFormView(FormView):
    """
    erpxFormView
    """

    class HttpResponse:
        """
        HttpResponse
        """

        def __new__(
            self, content: str = "", targets_to_reload: list = [], script: str = ""
        ) -> HttpResponse:
            """
            __new__ method
            """
            targets_to_reload = list(set(targets_to_reload))
            targets_to_reload.append("#reloadMessagesButton")
            script_id = get_short_uuid(4)
            script = (
                f"<script id='scriptTarget{script_id}'>"
                + "{}".format(
                    "".join([f"$(`{target}`).click();" for target in targets_to_reload])
                )
                + f"$('#scriptTarget{script_id}').closest('.oh-modal--show').first().removeClass('oh-modal--show');"
                + "$('.reload-record').click();"
                + "$('.reload-field').click();"
                + script
                + "</script>"
            )

            reload_response = HttpResponse(script).content

            user_response = HttpResponse(content).content
            response = HttpResponse(reload_response + user_response)
            self = response
            return response

    model: object = None
    view_id: str = get_short_uuid(4)
    hx_confirm: str = ""
    form_class: forms.ModelForm = None
    template_name = "generic/erpx_form.html"
    ids_key: str = "instance_ids"
    form_disaply_attr: str = ""
    new_display_title: str = "Add New"
    close_button_attrs: str = """"""
    submit_button_attrs: str = """"""

    # NOTE: Dynamic create view's forms save method will be overwritten
    is_dynamic_create_view: bool = False
    dynamic_create_fields: list = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        request = getattr(_thread_locals, "request", None)
        self.request = request
        if not self.success_url:
            self.success_url = self.request.path
        update_initial_cache(request, CACHE, erpxFormView)

        if self.form_class:
            setattr(self.form_class, "structured", structured)

    def get(
        self, request: HttpRequest, *args: str, pk=None, **kwargs: Any
    ) -> HttpResponse:
        _pk = pk
        response = super().get(request, *args, **kwargs)
        return response

    def post(
        self, request: HttpRequest, *args: str, pk=None, **kwargs: Any
    ) -> HttpResponse:
        _pk = pk
        self.get_form()
        response = super().post(request, *args, **kwargs)
        return response

    def init_form(self, *args, data={}, files={}, instance=None, **kwargs):
        """
        method where first the form where initialized
        """
        self.form_class: forms.ModelForm

        form = self.form_class(
            data, files, instance=instance, initial=self.get_initial()
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.form_class_path = (
            self.get_form().__class__.__module__ + "." + self.form.__class__.__name__
        )

        context["dynamic_create_fields"] = self.dynamic_create_fields
        context["form_class_path"] = self.form_class_path
        context["view_id"] = self.view_id
        context["hx_confirm"] = self.hx_confirm
        pk = None
        if self.form.instance:
            pk = self.form.instance.pk
        # next/previous option in the forms
        if pk and self.request.GET.get(self.ids_key):
            instance_ids = eval(str(self.request.GET.get(self.ids_key)))
            url = resolve(self.request.path)
            key = list(url.kwargs.keys())[0]
            url_name = url.url_name
            if instance_ids:
                previous_id, next_id = closest_numbers(instance_ids, pk)

                next_url = reverse(url_name, kwargs={key: next_id})
                previous_url = reverse(url_name, kwargs={key: previous_id})

                self.form.instance_ids = str(instance_ids)
                self.form.ids_key = self.ids_key

                self.form.next_url = next_url
                self.form.previous_url = previous_url
        return context

    def get_queryset(self):
        """
        method to get the instance for the form
        """
        pk = self.kwargs.get("pk")
        return self.model.objects.filter(pk=pk).first()

    def get_form(self, form_class=None):

        pk = self.kwargs.get("pk")
        if not hasattr(self, "form"):
            instance = self.get_queryset()
            data = None
            files = None
            if self.request.method == "POST":
                data = self.request.POST
                files = self.request.FILES
            form = self.init_form(data=data, files=files, instance=instance)
            if self.is_dynamic_create_view:
                setattr(type(form), "save", save)

            if self.request.method == "GET":
                [
                    (
                        "employee_id",
                        FormView,
                    )
                ]
                for dynamic_tuple in self.dynamic_create_fields:
                    view = dynamic_tuple[1]
                    view.display_title = "Dynamic create"
                    field = dynamic_tuple[0]
                    key = self.request.session.session_key + "cbv" + field
                    field_instance = form.instance._meta.get_field(field)
                    value = form.initial.get(field, [])

                    form_field = forms.ChoiceField
                    if isinstance(field_instance, models.models.ManyToManyField):
                        form_field = forms.MultipleChoiceField
                        if form.instance.pk is not None:
                            value = list(
                                getattr(form.instance, field).values_list(
                                    "id", flat=True
                                )
                            )
                    else:
                        value = getattr(getattribute(form.instance, field), "pk", value)

                    CACHE.set(
                        key,
                        {
                            "dynamic_field": field,
                            "value": value,
                            "model": form._meta.model,
                        },
                    )

                    from django.urls import path

                    from erpx.urls import urlpatterns

                    urlpatterns.append(
                        path(
                            f"dynamic-path-{field}-{self.request.session.session_key}",
                            view.as_view(),
                            name=f"dynamic-path-{field}-{self.request.session.session_key}",
                        )
                    )
                    queryset = form.fields[field].queryset
                    choices = [(instance.id, instance) for instance in queryset]
                    choices.insert(0, ("", "Select option"))
                    choices.append(("dynamic_create", "Dynamic create"))
                    attrs = form.fields[field].widget.attrs
                    form.fields[field] = form_field(
                        choices=choices,
                        label=form.fields[field].label,
                        required=form.fields[field].required,
                    )
                    form.fields[field].widget.attrs = attrs
                    form.initial[field] = value
            if pk:
                form.instance = instance
                title = str(instance)
                if self.form_disaply_attr:
                    title = getattribute(instance, self.form_disaply_attr)
                if instance:
                    self.form_class.verbose_name = title
            else:
                self.form_class.verbose_name = self.new_display_title
            form.close_button_attrs = self.close_button_attrs
            form.submit_button_attrs = self.submit_button_attrs
            CACHE.get(self.request.session.session_key + "cbv")[erpxFormView] = form
            self.form = form
        return self.form


@method_decorator(hx_request_required, name="dispatch")
class erpxNavView(TemplateView):
    """
    erpxNavView

    filter form submit button id: applyFilter
    """

    template_name = "generic/erpx_nav.html"

    nav_title: str = ""
    search_url: str = ""
    search_swap_target: str = ""
    search_input_attrs: str = ""
    search_in: list = []
    actions: list = []
    group_by_fields: list = []
    filter_form_context_name: str = ""
    filter_instance: FilterSet = None
    filter_instance_context_name: str = ""
    filter_body_template: str = ""
    view_types: list = []
    create_attrs: str = """"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxNavView)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_title"] = self.nav_title
        context["search_url"] = self.search_url
        context["search_swap_target"] = self.search_swap_target
        context["search_input_attrs"] = self.search_input_attrs
        context["group_by_fields"] = self.group_by_fields
        context["actions"] = self.actions
        context["filter_body_template"] = self.filter_body_template
        context["view_types"] = self.view_types
        context["create_attrs"] = self.create_attrs
        context["search_in"] = self.search_in
        context["filter_instance_context_name"] = self.filter_instance
        last_filter = CACHE.get(
            self.request.session.session_key + "last-applied-filter", {}
        )
        context["last_filter"] = dict(last_filter)
        if self.filter_instance:
            context[self.filter_form_context_name] = self.filter_instance.form
        context["active_view"] = models.ActiveView.objects.filter(
            path=self.request.path
        ).first()
        CACHE.get(self.request.session.session_key + "cbv")[erpxNavView] = context
        return context


@method_decorator(hx_request_required, name="dispatch")
class erpxProfileView(DetailView):
    """
    GenericerpxProfileView
    """

    template_name = "generic/erpx_profile_view.html"
    view_id: str = None
    filter_class: FilterSet = None

    # add these method under the model
    # get_avatar --> image/profile
    # get_subtitle --> Job position

    actions: list = []

    tabs: list = []

    def __init__(self, **kwargs: Any) -> None:
        self.url_prefix = str(self.__class__.__name__.lower())
        if not self.view_id:
            self.view_id = get_short_uuid(4)
        super().__init__(**kwargs)

        request = getattr(_thread_locals, "request", None)
        self.request = request
        update_initial_cache(request, CACHE, erpxProfileView)

        from erpx.urls import path, urlpatterns

        for tab in self.tabs:
            if not tab.get("url"):
                url = f"{self.url_prefix}-{tab['title']}"
                urlpatterns.append(
                    path(
                        url + "/<int:pk>/",
                        tab["view"],
                    )
                )
                tab["url"] = "/" + url + "/{pk}/"

        # hidden columns configuration

        existing_instance = models.ToggleColumn.objects.filter(
            user_id=request.user, path=request.path_info
        ).first()

        self.visible_tabs = self.tabs.copy()

        self.tabs_list = [(tab["title"], tab["title"]) for tab in self.visible_tabs]

        hidden_tabs = (
            [] if not existing_instance else existing_instance.excluded_columns
        )
        self.toggle_form = ToggleColumnForm(
            self.tabs_list,
            hidden_tabs,
        )
        for column in self.tabs_list:
            if column[1] in hidden_tabs:
                for tab in self.visible_tabs:
                    if tab["title"] == column[1]:
                        self.visible_tabs.remove(tab)

    @classmethod
    def add_tab(cls, tab: dict = None, index: int = None, tabs: list = None) -> None:
        """
        Tab adding method
        example tab arg look like
        tab = {
            "title":"About",
            "view" : views.about_tab,
            "accessibility": "path_to_your.accessibility", # path to your accessibility method

        }
        tabs = [tab,etc...]

        add_tab(tabs=tabs) / add_tab(tab=tab)
        """
        if tabs:
            cls.tabs = cls.tabs + tabs
        if tab:
            if index is None:
                cls.tabs.append(tab)
                return
            cls.tabs.index(index, tab)

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["instance"] = context["object"]
        context["tabs"] = self.tabs
        context["visible_tabs"] = self.visible_tabs
        context["toggle_form"] = self.toggle_form
        context["view_id"] = self.view_id
        active_tab = models.ActiveTab.objects.filter(
            created_by=self.request.user, path=self.request.path
        ).first()
        if active_tab:
            context["active_target"] = active_tab.tab_target
        instance_ids_str = self.request.GET.get("instance_ids")
        if not instance_ids_str:
            instance_ids_str = "[]"
        instance_ids = eval(instance_ids_str)
        if instance_ids:
            CACHE.set(
                f"{self.request.session.session_key}hpv-instance-ids", instance_ids
            )
        else:
            instance_ids = CACHE.get(
                f"{self.request.session.session_key}hpv-instance-ids"
            )
            instance_ids = instance_ids if instance_ids else []
        instances = self.model.objects.filter(id__in=instance_ids)
        context["instances"] = instances
        balance_count = instances.count() - 6
        if balance_count > 9:
            display_count = "9+"
        elif 1 < balance_count <= 9:
            display_count = f"{balance_count-1}+"
        else:
            display_count = None

        previous_id, next_id = closest_numbers(instance_ids, context["instance"].pk)
        url = resolve(self.request.path)
        key = list(url.kwargs.keys())[0]

        url_name = url.url_name
        next_url = reverse(url_name, kwargs={key: next_id})
        previous_url = reverse(url_name, kwargs={key: previous_id})
        context["instance_ids"] = str(instance_ids)
        if instance_ids:
            context["next_url"] = next_url
            context["previous_url"] = previous_url

        context["display_count"] = display_count
        context["actions"] = self.actions
        context["filter_class"] = self.filter_class
        cache = {
            "instances": context["instances"],
            "instance_ids": context["instance_ids"],
            "filter_class": context["filter_class"],
            "view_id": context["view_id"],
            "object": context["object"],
        }
        CACHE.set(f"{self.request.session.session_key}search_in_instance_ids", cache)
        return context
