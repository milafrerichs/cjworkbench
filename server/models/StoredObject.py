from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.dispatch import receiver
from django.utils import timezone
import os


# StoredObject is our persistence layer.
# Allows WfModules to store keyed, versioned binary objects
class StoredObject(models.Model):
    # delete stored data if WfModule deleted
    wf_module = models.ForeignKey('WfModule', related_name='stored_objects', on_delete=models.CASCADE)
    file = models.FileField()
    stored_at = models.DateTimeField('stored_at', default=timezone.now)
    name = models.CharField('name', default=None, max_length=255, null=True)
    size = models.IntegerField('size', default=None, null=True)
    uuid = models.CharField('uuid', default=None, max_length=255, null=True)

    @staticmethod
    def __filename_for_id(id):
        return str(id) + '.dat'

    @staticmethod
    def create(wf_module, text):
        file = default_storage.save(StoredObject.__filename_for_id(wf_module.id), ContentFile(bytes(text, 'UTF-8')))
        return StoredObject.objects.create(wf_module=wf_module, file=file, stored_at=timezone.now())

    def get_data(self):
        self.file.open(mode='rb')
        data = self.file.read()
        self.file.close()
        # copy to bytearray as data is a memoryview in prod, which has no decode method
        return bytearray(data).decode('UTF-8')

    # make a deep copy for another WfModule
    def duplicate(self, to_wf_module):
        if self.file.url.endswith('.dat'):
            new_file = default_storage.save(StoredObject.__filename_for_id(to_wf_module.id), self.file)
        else:
            new_file = default_storage.save(self.file.url, self.file)
        new_so = StoredObject.objects.create(wf_module=to_wf_module,
                                             stored_at=self.stored_at,
                                             file = new_file)
        return new_so

@receiver(models.signals.post_delete, sender=StoredObject)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    # Deletes file from filesystem when corresponding `StoredObject` object is deleted.
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)