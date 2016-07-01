from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.generic import ListView
from django.views.generic import DetailView

from .models import Post
from .forms import EmailPostForm, CommentForm


class PostListView(ListView):
    model = Post
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3


class PostDetailView(DetailView):
    model = Post

    def get_object(self, queryset=None):
        return self.model.objects.get(slug=self.kwargs['post'],
                                      status='published',
                                      publish__year=self.kwargs['year'],
                                      publish__month=self.kwargs['month'],
                                      publish__day=self.kwargs['day'],
                                      )


def post_list(request):
    object_list = Post.published.all()
    paginator = Paginator(object_list, 3)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post_list.html', {'posts': posts, 'page': page})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()
    return render(request, 'blog/post_detail.html', {'post': post,
                                                     'comments': comments,
                                                     'comment_form': comment_form,
                                                     'new_comment': new_comment})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, 'admin@myblog.com',[cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post_share.html', {'post': post,
                                                    'form': form,
                                                    'sent': sent})
