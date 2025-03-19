from django.shortcuts import render


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


def page_error_view(request):
    return render(None, '500.html', status=505)
