from service.models import Account, RepositoryConfig
from service.scripts.loadcsvjournals import load_csv_journal
from service.scripts.loadezbparticipants import upload_csv
from octopus.core import app
import os
from pathlib import Path
import glob


class LoadTestData:
    def __init__(self, test_data_dir):
        if not os.path.isdir(test_data_dir):
            raise NotADirectoryError
        self.test_data_dir = test_data_dir
        self.accounts = [
            {
                'email': 'MDPI@deepgreen.org',
                'role': ['publisher'],
                'password': 'publisher1_MDPI',
            }, {
                'email': 'Karger@deepgreen.org',
                'role': ['publisher'],
                'password': 'publisher1_Karger',
            }, {
                'email': 'Frontiers@deepgreen.org',
                'role': ['publisher'],
                'password': 'publisher1_Frontiers',
            }, {
                'email': 'SAGE@deepgreen.org',
                'role': ['publisher'],
                'password': 'publisher1_SAGE',
            }, {
                'email': 'wiley@deepgreen.org',
                'role': ['publisher'],
                'password': 'publisher1_Wiley',
            }, {
                'email': 'UBR@deepgreen.org',
                'role': ['repository'],
                'password': 'repository1_UBR',
                'repository': {
                    'name': 'Universität Regensburg',
                    'bibid': 'UBR',
                },
                'packaging': 'http://purl.org/net/sword/package/METSMODS',
            }, {
                'email': 'UBEN@deepgreen.org',
                'role': ['repository'],
                'password': 'repositorr1_UBEN',
                'repository': {
                    'name': 'Friedrich-Alexander-Universität Erlangen-Nürnberg',
                    'bibid': 'UBEN',
                },
                'packaging': 'http://purl.org/net/sword/package/OPUS4Zip',
            }, {
                'email': 'UBK@deepgreen.org',
                'role': ['repository'],
                'password': 'repository1_UBK',
                'repository': {
                    'name': 'Christian-Albrechts-Universität zu Kiel',
                    'bibid': 'UBK',
                },
                'packaging': 'http://purl.org/net/sword/package/SimpleZip',
            }, {
                'email': 'TUBB@deepgreen.org',
                'role': ['repository'],
                'password': 'repository1_TUBB',
                'repository': {
                    'name': 'Technische Universität Berlin',
                    'bibid': 'TUBB',
                },
                'packaging': 'http://purl.org/net/sword/package/SimpleZip',
            }, {
                'email': 'TFRD@deepgreen.org',
                'role': ['repository', 'subject_repository', 'match_all'],
                'password': 'repository1_TFRD',
                'repository': {
                    'name': 'Fachrepositorium Test',
                    'bibid': 'TFRD',
                },
            }
        ]
        self.license_files = [
            {
                'file': "EZB-NALIW-00493_AL_2019-02-07.csv",
                "type": "alliance"
            }, {
                'file': "EZB-NALIW-00495_AL_2019-02-07.csv",
                "type": "alliance"
            }, {
                'file': "EZB-NALIW-00496_AL_2019-02-07.csv",
                "type": "alliance"
            }, {
                'file': "EZB-NALIX-00498_AL_2019-02-07.csv",
                "type": "alliance"
            }, {
                'file': "EZB-NALJB-00504_NL_2019-05-15.csv",
                "type": "alliance"
            }, {
                "file": "EZB-NALJC-00505_NL_2019-05-15.csv",
                "type": "alliance"
            }, {
                "file": "PUB-FRONT-00001_OA_2020-12-16.csv",
                "type": "gold"
            }, {
                "file": "PUB-MDPI0-00001_OA_2018-11-14.csv",
                "type": "gold"
            }, {
                "file": "EZB-SAGE-00001_OA_2021-05-04.csv",
                "type": "alliance"
            }
        ]
        self.participant_files = [
            'EZB-NALIW-00493_OA_participants_current.csv',
            'EZB-NALIW-00495_OA_participants_current.csv',
            'EZB-NALIW-00496_OA_participants_current.csv',
            'EZB-NALIX-00498_OA_participants_current.csv',
            'EZB-NALJB-00504_NL_participants_current.csv',
            'EZB-NALJC-00505_NL_participants_current.csv',
            'EZB-SAGE-00001_OA_participants_2021-05-04.csv'
        ]


    def create_accounts(self):
        # Create 5 publisher accounts and 5 repository accounts
        new_count = 0
        for account in self.accounts:
            a = Account.pull_by_email(account['email'])
            if not a:
                a = Account()
                a.add_account(account)
                a.save()
                new_count += 1
            self.account['id'] = a.id
        return new_count

    # Upload affiliation files for each of the repository accounts
    def upload_affiliation_files(self):
        affiliation_files_dir = os.path.join(self.test_data_dir, 'Affiliations files')
        if not os.path.isdir(affiliation_files_dir):
            raise NotADirectoryError
        for account in self.accounts:
            if 'repository' not in account.get('role', []):
                continue
            if not account.get('id', None):
                continue
            csvfile = os.path.join(affiliation_files_dir, '#{fn}.csv'.format(fn=account.get('repository', {}).get('name', '')))
            if not os.path.isfile(csvfile):
                print('File does not exist - #{f} - skipping'.format(f=csvfile))
                continue
            rec = RepositoryConfig().pull_by_repo(account['id'])
            if rec is None:
                rec = RepositoryConfig()
                rec.repository = account['id']
            saved = rec.set_repo_config(csvfile=csvfile, encoding='utf-8', repository=account['id'])
            if not saved:
                print('Error adding repository config file #{f}').format(f=csvfile)
            return

    # Add license files
    def add_license_files(self):
        license_dir = os.path.join(self.test_data_dir, 'License Files/Test License Files')
        if not os.path.isdir(license_dir):
            print('Path to license files not found - #{f}'.format(f=license_dir))
            return
        for l in self.license_files:
            license_file = os.path.join(license_dir, l['file'])
            if not os.path.isfile(license_file):
                print('License file not found - #{f}'.format(f=license_file))
                continue
            load_csv_journal(license_file, l['type'])
        return

    # Add participant (alliance) files
    def add_participant_files(self):
        participant_dir = os.path.join(self.test_data_dir, 'License Files/Test License Files')
        if not os.path.isdir(participant_dir):
            print('Path to participant files not found - #{f}'.format(f=participant_dir))
            return
        for p in self.participant_files:
            participant_file = os.path.join(participant_dir, p)
            if not os.path.isfile(participant_file):
                print('Participant file not found - #{f}'.format(f=participant_file))
                continue
            n = p.find('_')
            participant_id = p[:n].upper()
            upload_csv(participant_file, participant_id)

    def copy_files(self):
        # ToDo
        pubstoredir = app.config.get('PUBSTOREDIR', '/data/dg_storage')
        owner = app.config.get('PUBSTORE_USER', 'green')
        if not os.path.isdir(pubstoredir):
            print('Directory #{f} does not exists'.format(f=pubstoredir))
            raise NotADirectoryError
        p = Path(pubstoredir)
        if p.owner() != owner and p.group() != owner:
            print('User #{u} needs to be owner of #{f}'.format(u=owner, f=pubstoredir))
            raise PermissionError

        # for file in glob.glob('/mydir/apple*.json.gz'):
        #     print file