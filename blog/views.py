from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from blog.models import BlogPost


class BlogListView(ListView):
    """Отображение списка опубликованных статей блога (доступно всем)."""
    model = BlogPost
    template_name = "blog/blog_list.html"
    context_object_name = "posts"

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True)


class BlogDetailView(DetailView):
    """Детальный просмотр статьи с автоматическим увеличением счетчика просмотров."""
    model = BlogPost
    template_name = "blog/blog_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views_count += 1
        obj.save(update_fields=["views_count"])
        return obj


class BlogCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание статьи (только для Менеджеров и Администраторов)."""
    model = BlogPost
    fields = ("title", "content", "image", "is_published")
    template_name = "blog/blog_form.html"
    success_url = reverse_lazy("blog:list")

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name="Менеджер").exists()


class BlogUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование статьи (только для Менеджеров и Администраторов)."""
    model = BlogPost
    fields = ("title", "content", "image", "is_published")
    template_name = "blog/blog_form.html"

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name="Менеджер").exists()

    def get_success_url(self):
        return reverse("blog:detail", kwargs={"pk": self.object.pk})


class BlogDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Удаление статьи (только для Менеджеров и Администраторов)."""
    model = BlogPost
    template_name = "blog/blog_confirm_delete.html"
    success_url = reverse_lazy("blog:list")

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name="Менеджер").exists()
