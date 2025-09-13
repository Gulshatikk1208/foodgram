from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from foodgram_backend import constants


class User(AbstractUser):
    """Абстрактная модель пользователя."""

    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True,
        max_length=constants.EMAIL_MAX_LENGTH
    )

    avatar = models.ImageField(
        upload_to='users/images',
        verbose_name='Аватар',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def clean(self):
        super().clean()
        if self.username.lower() == 'me':
            raise ValidationError('Выберите другое имя для пользователя.')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Follow(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_follow'
            ),
        ]
        ordering = ('id',)

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на себя.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} подписан на {self.following}'
