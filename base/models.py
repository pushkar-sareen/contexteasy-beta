from django.db import models
from pathlib import Path

# Create your models here.

class Chat(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='chats', null=True, blank=True)
    user_input = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.id} - {self.created_at}"
    

class DatabaseChat(models.Model):
    user_input = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat {self.id} - {self.created_at}"
    
class DataFiles(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DataFiles {self.id} - {self.uploaded_at}"



def user_upload_path(instance, filename):
    return f"uploads/{instance.user.email}/{filename}"


class UploadedFile(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="uploaded_files",
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to=user_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    

class UploadedBackup(models.Model):
    file = models.FileField(upload_to="backup/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    


class YoutbeLink(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='youtubelink', null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.name
    
class URLLink(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='urldata', null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.name

class DatabaseLink(models.Model):
    name = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name