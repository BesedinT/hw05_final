from django.conf import settings
from django.core.paginator import Paginator

POSTS_OF_PAGE = settings.POSTS_OF_PAGE


def page_context(request, post_list):
    paginator = Paginator(post_list, POSTS_OF_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
