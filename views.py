import os
import re
import uuid

from core.models import Job, Page
from django.core import management
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser


@api_view(['GET'])
def description(request):
    """
    api/admin/
    API description response with URLs to list resources
    """
    description = {
        'description': 'Open ONI Admin API for automating management tasks',
        'title': 'Open ONI Admin API',
    }
    return JsonResponse(description, safe=False)


@api_view(['POST'])
@parser_classes([JSONParser])
def batch_load(request):
    """
    api/admin/batch/load
    Load a batch into the database, word coordinates files, and Solr index
    """
    batch_path = request.data['batch_path'].rstrip("/")
    _, batch_name = os.path.split(batch_path)
    if not valid_batch_name(batch_name):
        return JsonResponse({'info': 'Invalid batch path'}, status=status.HTTP_400_BAD_REQUEST)
    elif not os.path.exists(batch_path):
        return JsonResponse({'info': 'Batch does not exist'}, status=status.HTTP_404_NOT_FOUND)

    job_in_progress = Job.objects.filter(info=batch_name, status=Job.Status.IN_PROGRESS)
    if job_in_progress.count() > 0:
        return JsonResponse({
            'info': 'Job for %s already in progress' % batch_name,
            'job_id': job_in_progress.first().id,
        }, status=status.HTTP_409_CONFLICT, headers={'Retry-After': 120})

    try:
        management.call_command('load_batch', batch_path, interactive=False)
    except Exception as e:
        if str(e).startswith('Batch already loaded:'):
            return JsonResponse({'info': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            return JsonResponse({'info': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    load_job = Job.objects.filter(type=Job.Type.LOAD_BATCH, info=batch_name)
    if load_job.count() > 0:
        load_job = load_job.first()
        load_status = Job.Status(load_job.status).label
        job_id = load_job.id
    else:
        load_status = "Attempt failed"
        job_id = "N/A"
    return JsonResponse({'info': 'Batch load attempted', 'job_id': job_id, 'status': load_status})


@api_view(['POST'])
@parser_classes([JSONParser])
def batch_purge(request):
    """
    api/admin/batch/purge
    Purge a batch from database, word coordinates files, and Solr index
    """
    batch_name = request.data['batch_name']
    if not valid_batch_name(batch_name):
        return JsonResponse({'info': 'Invalid batch name'}, status=status.HTTP_400_BAD_REQUEST)

    job_in_progress = Job.objects.filter(info=batch_name, status=Job.Status.IN_PROGRESS)
    if job_in_progress.count() > 0:
        return JsonResponse({
            'info': 'Job for %s already in progress' % batch_name,
            'job_id': job_in_progress.first().id,
        }, status=status.HTTP_409_CONFLICT, headers={'Retry-After': 30})

    try:
        management.call_command('purge_batch', batch_name, interactive=False)
    except Exception as e:
        if str(e).startswith('Tried to purge batch that does not exist:'):
            return JsonResponse({'info': str(e)}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({'info': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    purge_job = Job.objects.filter(type=Job.Type.PURGE_BATCH, info=batch_name)
    if purge_job.count() > 0:
        purge_job = purge_job.first()
        purge_status = Job.Status(purge_job.status).label
        job_id = purge_job.id
    else:
        purge_status = "Attempt failed"
        job_id = "N/A"
    return JsonResponse({'info': 'Batch purge attempted', 'job_id': job_id, 'status': purge_status})


@api_view(['GET'])
def job_status(request, job_id):
    """
    api/admin/job/status/<job_id>
    Respond with status of job specified by job_id
    """
    if not valid_job_id(job_id):
        return JsonResponse({'info': 'Invalid job id'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        job = Job.objects.get(id=job_id)
        info = {
            'info': job.info,
            'status': Job.Status(job.status).label,
        }

        if Job.Status(job.status) == 'In Progress' and Job.Type(job.type).label == 'Batch':
            info['page_count'] = Page.objects.filter(issue__batch__id=job_id).count()
    except Exception as e:
        if str(e).startswith('Job matching query does not exist.'):
            return JsonResponse({'info': str(e)}, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({'info': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse(info, safe=False)


def valid_batch_name(batch_name):
    if len(batch_name) == 0:
        return False

    try:
        batch, org_code, name, version = batch_name.split("_", 3)
    except ValueError:
        return False

    if batch != 'batch':
        return False
    elif not re.fullmatch(r'[a-z]+', org_code):
        return False
    elif not re.fullmatch(r'\w+', name):
        return False
    elif not re.fullmatch(r'ver\d{2}', version):
        return False
    else:
        return True


def valid_job_id(job_id):
    try:
        uuid.UUID(job_id)
    except ValueError:
        return False

    return True
