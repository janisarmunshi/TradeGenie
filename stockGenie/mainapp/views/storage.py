from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import gspread

GOOGLE_SHEET_AUTH_DICT = {
    "type": "service_account",
    "project_id": "dhananjay-finserv",
    "private_key_id": "a92fbba0f1ebfea844493928119263510371f623",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDFBv9O7DJEkDnm\nLP0ZEAkEuK5k7+EEi/GXZUBd0DXKQNHfvNIc6rIpeLc66ELdkeRsVsTy6AgwQkQy\nab//HO2rtuORnCWXtvybIyn2U6j+C9E8haJTFOo8mhP6pUaqv8y19nGlismYoFum\n0F71F2QXqe6u3GGFkoHRXi/c523TMEtNn/s2/aGItzA4YZXvcW70DyRpW8xMY1nP\n5dOHrs6oU0SgU/tix1cVz0UMF67GhwkiN37tZqRRJ0pUh186Gz9HeSpE1oZkiXOc\n+f0QZh2ml1yvRMqPPmCC1ZatbDoeT3KMYMM74my9+iTSlur1CPBGVqDb0bXcUFnr\n5NzI5K2dAgMBAAECggEAPz9lycIMyPG7hGZAwUDihD98zC4s/7ak0ULRjMv/2HNC\nbB5DHMFCfAmiWCii/lmNCDI6evd9WXCMT9qepZh1uz+0gdOsRa2aHXsGR2rHvvWw\nL0t+tkjqgJW9gCJ6MunrHyaDiO6qlHI1ubD+KpNdsDL+yec47xX+0mT33GP2X2p7\nBnIztwBRR6XzU/L3ygUE+QxG/5xzJwhzdy9T+8mAdzBOWC/Sy6F3kCCtGfP8cxBE\nBEpSbuDWrRb9aUVUhwgnk3qEPhHg8QiJPw8DEui8vrkGMDkGPZXJcjm2frwVXGxd\nj+Mz4iwbaDNFwhRJ5BdfpZogPZacQShkvZ97atTHyQKBgQDro7NnvPawHDxHWzPA\nfcCi5KYVF90Z8aJnuwftga8WeM9X6iH9Qhe4hjpS0oLjmgkRg8BPelvGVT8I/kOA\n1iGeat57fZD0eVoOPeFDGf6JHcorGk1rbi1AAkFLMSkmxTup53aLJyYSqMqE4YjB\nXoI3/AHoaxvUjN3m+7PsraGxgwKBgQDWDTQsXvCS8sGYswxZb32OStNvmLYgfD8B\nOTdreTdThQzZjXQH92hMNa2oVJT7wwgQ7DGMc1GrK15IfSV/qrbXKW9LHJI4DkLQ\nPWMGgMlewaGL58Uicyesuz3RKaGTHE+zkLr1phmqK/tAkrmRVOYGw9kRB7XuQqmM\nilzgsomaXwKBgQDkHwjSBzfy6oLYucxyL8vMZvr6NK4SLcGCFqjoH8I3SSHCBKJ/\nIfsA4sGX6MBaQ4c/84K77sLmUSTDOhRzp9nIGcHlX3xzkP/EBdgMNCAc8kAEVmRY\n+sLH0ucPOjqSlCLcq34x3OaY7duRpR3Vxf7e4BOgxACfVviEY2yeVsHQrQKBgA5d\nSHkJzf8uh0tmCJgf4T8hSlsc1mwLqna8jjmKIupZ7WjUE0tNkRQ8LfEz6+ORTQNF\ntnWEb6CbAnK+4ztUC30Y7L0Pp8hXPKiY1gJjth/DwsGOxi3vqGPxFM7qiktDBR45\nwjIl+WbwGKZWsllMZztg/TolWFIq6xHhXyY9FPrlAoGAfgX80pvFPredrQMxEaS0\n0qFoejhaJmaxJwUrEcnJDMK3iZ9CMTffP6lbm6i2PqSvNCsKeV0lkyahdJxAk88z\neDFoaSPGcnbskTxXOxOlCu9fui9EOfchY1PV+PXLcNByPBps5AozVFchaSDl/Yaz\nVY9MovuYhHT9Y3HTz5Sd6ek=\n-----END PRIVATE KEY-----\n",
    "client_email": "mudra-services@dhananjay-finserv.iam.gserviceaccount.com",
    "client_id": "118164358053462144807",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mudra-services%40dhananjay-finserv.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}


class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/

        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):

        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super(MyModelName, self).save(*args, **kwargs)
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
    
class GoogleSheetAPI():
    def getGoogleSheet(docname):
        gc = gspread.service_account_from_dict(GOOGLE_SHEET_AUTH_DICT)
        sh = gc.open(docname).sheet1
        return sh
        # df = pd.DataFrame(sh.get())
