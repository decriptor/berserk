
from south.db import db
from django.db import models
from berserk2.sprints.models import *

class Migration:

    def forwards(self, orm):

        # Changing field 'MilestoneStatisticsCache.total_open_tasks'
        db.alter_column('sprints_milestonestatisticscache', 'total_open_tasks', models.IntegerField(default=0))

        # Changing field 'MilestoneStatisticsCache.total_estimated_hours'
        db.alter_column('sprints_milestonestatisticscache', 'total_estimated_hours', models.IntegerField(default=0))

        # Changing field 'MilestoneStatisticsCache.total_remaining_hours'
        db.alter_column('sprints_milestonestatisticscache', 'total_remaining_hours', models.IntegerField(default=0))



    def backwards(self, orm):

        # Changing field 'MilestoneStatisticsCache.total_open_tasks'
        db.alter_column('sprints_milestonestatisticscache', 'total_open_tasks', models.IntegerField())

        # Changing field 'MilestoneStatisticsCache.total_estimated_hours'
        db.alter_column('sprints_milestonestatisticscache', 'total_estimated_hours', models.IntegerField())

        # Changing field 'MilestoneStatisticsCache.total_remaining_hours'
        db.alter_column('sprints_milestonestatisticscache', 'total_remaining_hours', models.IntegerField())



    models = {
        'sprints.tasksnapshot': {
            'Meta': {'get_latest_by': "'date'"},
            'actual_hours': ('models.IntegerField', [], {}),
            'assigned_to': ('models.ForeignKey', ['User'], {'related_name': "'assigned_to'", 'null': 'True', 'db_index': 'True'}),
            'component': ('models.CharField', [], {'max_length': '128'}),
            'date': ('models.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True'}),
            'estimated_hours': ('models.IntegerField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'remaining_hours': ('models.IntegerField', [], {}),
            'status': ('models.CharField', [], {'max_length': '32'}),
            'submitted_by': ('models.ForeignKey', ['User'], {'related_name': "'submitted_by'", 'null': 'True'}),
            'task': ('models.ForeignKey', ['Task'], {'db_index': 'True'}),
            'title': ('models.CharField', [], {'max_length': '128'})
        },
        'sprints.task': {
            'Meta': {'unique_together': "(('remote_tracker_id','bug_tracker'),)"},
            'bug_tracker': ('models.ForeignKey', ['BugTracker'], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'remote_tracker_id': ('models.CharField', [], {'max_length': '32'}),
            'sprints': ('models.ManyToManyField', ['Sprint'], {'blank': 'True'})
        },
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'sprints.milestone': {
            'Meta': {'get_latest_by': "'-end_date'"},
            'bug_tracker': ('models.ForeignKey', ['BugTracker'], {}),
            'end_date': ('models.DateField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', [], {'max_length': '128'}),
            'remote_tracker_name': ('models.CharField', [], {'max_length': '128'}),
            'start_date': ('models.DateField', [], {})
        },
        'sprints.tasksnapshotcache': {
            'Meta': {'unique_together': "(('date','task_snapshot'),)"},
            'date': ('models.DateField', [], {'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'task_snapshot': ('models.ForeignKey', ['TaskSnapshot'], {'db_index': 'True'})
        },
        'sprints.sprint': {
            'Meta': {'ordering': "['-end_date']", 'get_latest_by': "'end_date'"},
            'default_bug_tracker': ('models.ForeignKey', ['BugTracker'], {'null': 'True'}),
            'end_date': ('models.DateField', [], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('models.ForeignKey', ['Milestone'], {'null': 'True', 'blank': 'True'}),
            'start_date': ('models.DateField', [], {}),
            'velocity': ('models.IntegerField', [], {'default': '6'})
        },
        'sprints.milestonestatisticscache': {
            'Meta': {'unique_together': "(('date','milestone'),)"},
            'date': ('models.DateField', [], {'auto_now_add': 'True', 'db_index': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'milestone': ('models.ForeignKey', ['Milestone'], {}),
            'total_estimated_hours': ('models.IntegerField', [], {'default': '0'}),
            'total_open_tasks': ('models.IntegerField', [], {'default': '0'}),
            'total_remaining_hours': ('models.IntegerField', [], {'default': '0'})
        },
        'sprints.bugtracker': {
            'Meta': {'unique_together': "(('base_url','product','backend'),)"},
            'backend': ('models.CharField', [], {'max_length': '32'}),
            'base_url': ('models.CharField', [], {'max_length': '256', 'verbose_name': "'Bugzilla Base URL'"}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'password': ('models.CharField', [], {'max_length': '32'}),
            'product': ('models.CharField', [], {'max_length': '128', 'verbose_name': "'Product Name'"}),
            'username': ('models.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['sprints']
