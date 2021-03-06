from datetime import date
from django.db import connection, backend, models

class SprintManager(models.Manager):
    def current(self, project):
        """
        Returns the current Sprint for the given project, or None if there is
        no current sprint.
        """
        today = date.today()
        sprint = self.filter(start_date__lte=today, end_date__gte=today,
                             project=project)
        if sprint.count() == 0:
            return None
        elif sprint[0].is_active():
            return sprint[0]
        else:
            return None
