from django.db import models

# Create your models here.


from django.db import models

# Create your models here.

class ChatData(models.Model):
    user_chat = models.CharField(max_length=255)
    response_chat = models.CharField(max_length=255)
    time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_chat