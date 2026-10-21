import secrets
import platform
import subprocess
import time
import django
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


def get_git_info():
    """Retrieve git branch and short commit information safely."""
    info = {
        'branch': 'main',
        'commit_short': 'ffccd84',
        'commit_msg': 'feat: CADverse platform backend',
    }
    try:
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if branch:
            info['branch'] = branch

        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if commit:
            info['commit_short'] = commit

        msg = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%B'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if msg:
            info['commit_msg'] = msg.split('\n')[0]
    except Exception:
        pass
    return info


def terminal_status_view(request):
    """Render terminal-style project status page at root URL."""
    # Measure live database connectivity & latency
    db_status = "Connected"
    db_latency = "< 20"
    try:
        t0 = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_latency = f"{round((time.time() - t0) * 1000, 1)}"
    except Exception:
        db_status = "Disconnected / Sleeping"
        db_latency = "N/A"

    git_info = get_git_info()
    host_name = request.get_host()

    context = {
        'platform_name': f"{platform.system()} ({platform.release()}) / Render Cloud",
        'python_version': platform.python_version(),
        'django_version': django.get_version(),
        'host_name': host_name,
        'db_engine': "Supabase PostgreSQL (Pooled)",
        'db_status': db_status,
        'db_latency': db_latency,
        'git_branch': git_info['branch'],
        'git_commit_short': git_info['commit_short'],
        'git_commit_message': git_info['commit_msg'],
    }
    return render(request, 'terminal_status.html', context)


@require_GET
def database_keepalive(request):
    expected_token = getattr(settings, "SUPABASE_KEEPALIVE_TOKEN", "")
    provided_token = request.headers.get(
        "X-Keepalive-Token", ""
    )

    if not expected_token or not secrets.compare_digest(
        provided_token, expected_token
    ):
        return JsonResponse(
            {"error": "Unauthorized"},
            status=403,
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM django_migrations"
            )
            cursor.fetchone()
        return JsonResponse({
            "status": "ok",
            "database": "connected",
        })
    except Exception:
        return JsonResponse(
            {"status": "error", "database": "unavailable"},
            status=503,
        )
