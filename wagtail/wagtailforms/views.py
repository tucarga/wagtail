import datetime
import json
import unicodecsv

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.text import capfirst
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import FormSubmission, get_form_types
from wagtail.wagtailforms.forms import SelectDateForm


def get_form_type_from_url_params(app_name, model_name):
    """
    Retrieve a form type from an app_name / model_name combo.
    Throw Http404 if not a valid form type
    """
    try:
        content_type = ContentType.objects.get_by_natural_key(app_name, model_name)
    except ContentType.DoesNotExist:
        raise Http404
    if content_type not in get_form_types():
        raise Http404

    return content_type


@permission_required('wagtailadmin.access_admin')
def index(request):
    form_types = get_form_types()
    form_pages = Page.objects.filter(content_type__in=form_types)

    return render(request, 'wagtailforms/index.html', {
        'form_pages': form_pages,
    })


@permission_required('wagtailadmin.access_admin')
def list_submissions(request, app_label, model, page_id):
    form_page = get_object_or_404(Page, id=page_id)

    submissions = FormSubmission.objects.filter(page=form_page)

    select_date_form = SelectDateForm(request.GET)
    if select_date_form.is_valid():
        date_from = select_date_form.cleaned_data.get('date_from')
        date_to = select_date_form.cleaned_data.get('date_to')
        # careful: date_to should be increased by 1 day since the submit_time
        # is a time so it will always be greater
        if date_to:
            date_to += datetime.timedelta(days=1)
        if date_from and date_to:
            submissions = submissions.filter(submit_time__range=[date_from, date_to])
        elif date_from and not date_to:
            submissions = submissions.filter(submit_time__gte=date_from)
        elif not date_from and date_to:
            submissions = submissions.filter(submit_time__lte=date_to)

    if request.GET.get('action') == 'CSV':
        # return a CSV instead
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export.csv'
        writer = unicodecsv.writer(response, encoding='utf-8')

        if submissions:
            extra_keys = json.loads(submissions[0].form_data).keys()

        header_row = ['Submission date', 'user']
        header_row.extend(extra_keys)
        writer.writerow(header_row)
        for s in submissions:
            data_row = [s.submit_time, s.user]
            form_data = json.loads(s.form_data)
            for ek in extra_keys:
                data_row.append(form_data.get(ek))
            writer.writerow(data_row)
        return response

    p = request.GET.get('p', 1)
    paginator = Paginator(submissions, 20)

    try:
        submissions = paginator.page(p)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    return render(request, 'wagtailforms/form_index.html', {
         'form_page': form_page,
         'select_date_form': select_date_form,
         'submissions': submissions,
    })