"""
context_processor.py

This module is used to register context processor`
"""

from django.apps import apps
from django.http import HttpResponse
from django.urls import path

from base.models import Company, TrackLateComeEarlyOut
from base.urls import urlpatterns
from employee.models import EmployeeGeneralSetting
from erpx import erpx_apps
from erpx.decorators import hx_request_required, login_required, permission_required
from erpx.methods import get_erpx_model_class


class AllCompany:
    """
    Dummy class
    """

    class Urls:
        url = "/static/favicons/favicon.png"

    company = "ERPX"
    icon = Urls()
    text = "ERPX PLATFORM"
    id = None


def get_companies(request):
    """
    This method will return the history additional field form
    """
    companies = list(
        [company.id, company.company, company.icon.url, False]
        for company in Company.objects.all()
    )
    companies = [
        [
            "all",
            "ERPX PLATFORM",
            "/static/favicons/favicon.png",
            False,
        ],
    ] + companies
    selected_company = request.session.get("selected_company")
    company_selected = False
    if selected_company and selected_company == "all":
        companies[0][3] = True
        company_selected = True
    else:
        for company in companies:
            if str(company[0]) == selected_company:
                company[3] = True
                company_selected = True
    return {"all_companies": companies, "company_selected": company_selected}


@login_required
@hx_request_required
@permission_required("base.change_company")
def update_selected_company(request):
    """
    This method is used to update the selected company on the session
    """
    company_id = request.GET.get("company_id")
    request.session["selected_company"] = company_id
    company = (
        AllCompany()
        if company_id == "all"
        else (
            Company.objects.filter(id=company_id).first()
            if Company.objects.filter(id=company_id).first()
            else AllCompany()
        )
    )

    text = "ERPX PLATFORM"
    if company_id == request.user.employee_get.employee_work_info.company_id:
        text = "My Company"
    if company_id == "all":
        text = "ERPX PLATFORM"
    company = {
        "company": company.company,
        "icon": company.icon.url,
        "text": text,
        "id": company.id,
    }
    request.session["selected_company_instance"] = company
    return HttpResponse("<script>window.location.reload();</script>")


urlpatterns.append(
    path(
        "update-selected-company",
        update_selected_company,
        name="update-selected-company",
    )
)


def white_labelling_company(request):
    white_labelling = getattr(erpx_apps, "WHITE_LABELLING", False)
    if white_labelling:
        hq = Company.objects.filter(hq=True).last()
        try:
            company = (
                request.user.employee_get.get_company()
                if request.user.employee_get.get_company()
                else hq
            )
        except:
            company = hq

        return {
            "white_label_company_name": company.company if company else "ERPX",
            "white_label_company": company,
        }
    else:
        return {
            "white_label_company_name": "ERPX",
            "white_label_company": None,
        }


def resignation_request_enabled(request):
    """
    Check weather resignation_request enabled of not in offboarding
    """
    enabled_resignation_request = False
    first = None
    if apps.is_installed("offboarding"):
        OffboardingGeneralSetting = get_erpx_model_class(
            app_label="offboarding", model="offboardinggeneralsetting"
        )
        first = OffboardingGeneralSetting.objects.first()
    if first:
        enabled_resignation_request = first.resignation_request
    return {"enabled_resignation_request": enabled_resignation_request}


def timerunner_enabled(request):
    """
    Check weather resignation_request enabled of not in offboarding
    """
    first = None
    enabled_timerunner = True
    if apps.is_installed("attendance"):
        AttendanceGeneralSetting = get_erpx_model_class(
            app_label="attendance", model="attendancegeneralsetting"
        )
        first = AttendanceGeneralSetting.objects.first()
    if first:
        enabled_timerunner = first.time_runner
    return {"enabled_timerunner": enabled_timerunner}


def intial_notice_period(request):
    """
    Check weather resignation_request enabled of not in offboarding
    """
    initial = 30
    first = None
    if apps.is_installed("payroll"):
        PayrollGeneralSetting = get_erpx_model_class(
            app_label="payroll", model="payrollgeneralsetting"
        )
        first = PayrollGeneralSetting.objects.first()
    if first:
        initial = first.notice_period
    return {"get_initial_notice_period": initial}


def check_candidate_self_tracking(request):
    """
    This method is used to get the candidate self tracking is enabled or not
    """

    candidate_self_tracking = False
    if apps.is_installed("recruitment"):
        RecruitmentGeneralSetting = get_erpx_model_class(
            app_label="recruitment", model="recruitmentgeneralsetting"
        )
        first = RecruitmentGeneralSetting.objects.first()
    else:
        first = None
    if first:
        candidate_self_tracking = first.candidate_self_tracking
    return {"check_candidate_self_tracking": candidate_self_tracking}


def check_candidate_self_tracking_rating(request):
    """
    This method is used to check enabled/disabled of rating option
    """
    rating_option = False
    if apps.is_installed("recruitment"):
        RecruitmentGeneralSetting = get_erpx_model_class(
            app_label="recruitment", model="recruitmentgeneralsetting"
        )
        first = RecruitmentGeneralSetting.objects.first()
    else:
        first = None
    if first:
        rating_option = first.show_overall_rating
    return {"check_candidate_self_tracking_rating": rating_option}


def get_initial_prefix(request):
    """
    This method is used to get the initial prefix
    """
    settings = EmployeeGeneralSetting.objects.first()
    instance_id = None
    prefix = "PEP"
    if settings:
        instance_id = settings.id
        prefix = settings.badge_id_prefix
    return {"get_initial_prefix": prefix, "prefix_instance_id": instance_id}


def biometric_app_exists(request):
    from django.conf import settings

    biometric_app_exists = "biometric" in settings.INSTALLED_APPS
    return {"biometric_app_exists": biometric_app_exists}


def enable_late_come_early_out_tracking(request):
    tracking = TrackLateComeEarlyOut.objects.first()
    enable = tracking.is_enable if tracking else True
    return {"tracking": enable, "late_come_early_out_tracking": enable}
