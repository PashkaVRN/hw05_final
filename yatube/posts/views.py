from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User, FollowGroup
from .utils import paginator
from django.db.models import Q


def index(request):
    posts_list = Post.objects.select_related('group', 'author').all()
    context = {
        'page_obj': paginator(request, posts_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.select_related('author').all()
    followin = request.user.is_authenticated and group.followin.filter(
        user=request.user).exists()
    context = {
        'group': group,
        'page_obj': paginator(request, posts_list),
        'followin': followin
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    following = request.user.is_authenticated and author.following.filter(
        user=request.user).exists()
    context = {
        'author': author,
        'page_obj': paginator(request, post_list),
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm()
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk,)
    post.delete()
    return redirect('posts:profile', post.author)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post.pk,)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related('author', 'group').filter(
        Q(author__following__user=request.user)
        | Q(group__followin__user=request.user))
#   post_list = Post.objects.filter(author__in=follow_list.values('author'))
    context = {'page_obj': paginator(request, post_list)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user, author__username=username).delete()
    return redirect('posts:profile', username)


@login_required
def group_follow(request, slug):
    group = get_object_or_404(Group, slug=slug)
    if not FollowGroup.objects.filter(user=request.user, group=group).exists():
        new_follow = FollowGroup(user=request.user, group=group)
        new_follow.save()
    return redirect('posts:group_list', slug=slug)


@login_required
def group_unfollow(request, slug):
    group = get_object_or_404(Group, slug=slug)
    follows = FollowGroup.objects.filter(user=request.user, group=group)
    if follows.exists():
        follows.delete()
    return redirect('posts:group_list', slug=slug)
