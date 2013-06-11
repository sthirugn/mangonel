from basetest import BaseTest

from katello.client.server import ServerRequestError

from mangonel.changeset import Changeset
from mangonel.contentview import ContentView
from mangonel.contentviewdefinition import ContentViewDefinition
from mangonel.environment import Environment
from mangonel.organization import Organization
from mangonel.product import Product
from mangonel.provider import Provider
from mangonel.repository import Repository
from mangonel.system import System
from mangonel.server import Server

import time
import unittest

class TestStress(BaseTest):

    def setUp(self):
        BaseTest.setUp(self)

        self.server = Server(host=self.host,
                       project=self.project,
                       username=self.user,
                       password=self.password)
        self.org_api = Organization()
        self.chs_api = Changeset()
        self.cv_api = ContentView()
        self.cvd_api = ContentViewDefinition()
        self.env_api = Environment()
        self.prd_api = Product()
        self.prv_api = Provider()
        self.repo_api = Repository()
        self.sys_api = System()

        self.start_time = time.time()


    def tearDown(self):
        self.server = None

        self.ellapsed_time = time.time() - self.start_time
        self.logger.info("Test ellapsed time: %s" % self.ellapsed_time)


    def test_stress_128_1(self):
        "Creates a new organization with environment and register a system."

        org = self.org_api.create_org()
        self.logger.debug("Created organization %s" % org['name'])
        self.assertEqual(org, self.org_api.organization(org['name']), 'Failed to create and retrieve org.')

        env1 = self.env_api.create_environment(org, 'Dev', 'Library')
        self.logger.debug("Created environmemt %s" % env1['name'])
        self.assertEqual(env1, self.env_api.environment_by_name(org, 'Dev'))

        env2 = self.env_api.create_environment(org, 'Testing', 'Dev')
        self.logger.debug("Created environmemt %s" % env2['name'])
        self.assertEqual(env2, self.env_api.environment_by_name(org, 'Testing'))

        env3 = self.env_api.create_environment(org, 'Release', 'Testing')
        self.logger.debug("Created environmemt %s" % env3['name'])
        self.assertEqual(env3, self.env_api.environment_by_name(org, 'Release'))

        prv = self.prv_api.create_provider(org, 'Provider1')
        self.logger.debug("Created custom provider Provider1")
        self.assertEqual(prv, self.prv_api.provider(prv['id']))

        prd = self.prd_api.create_product(prv, 'Product1')
        self.logger.debug("Created product Product1")
        self.assertEqual(prd, self.prd_api.product(org, prd['id']))

        repo = self.repo_api.create_repository(org, prd, 'http://hhovsepy.fedorapeople.org/fakerepos/zoo4/', 'Repo1')
        self.logger.debug("Created repositiry Repo1")
        self.assertEqual(repo, self.repo_api.repository(repo['id']))

        # Sync
        self.prv_api.sync(prv['id'])
        self.assertEqual(self.prv_api.provider(prv['id'])['sync_state'], 'finished')
        self.logger.debug("Finished synchronizing Provider1")

        # Content View Definition
        cvd = self.cvd_api.create_content_view_definition(org, 'CVD1')
        prods = self.cvd_api.update_products(org, cvd['id'], prd)
        
        # Published Content view
        self.cvd_api.publish(org, cvd['id'], 'PublishedCVD1')
        pcvd = self.cv_api.content_views_by_label_name_or_id(org['label'], name='PublishedCVD1')

        # Changeset
        chs = self.chs_api.create(org, env1, 'Promote01')
        self.chs_api.add_content(chs['id'], pcvd)
        self.chs_api.apply(chs['id'])
        
        system_time = time.time()
        for idx in range(128):
            sys1 = self.sys_api.create_system(org, env)
            self.logger.debug("Created system %s" % sys1['uuid'])
            self.assertEqual(sys1['uuid'], self.sys_api.system(sys1['uuid'])['uuid'])
        total_system_time = time.time() - system_time
        print "Total time spent for systems: %f" % total_system_time
        print "Mean time: %f" % total_system_time / 128

        self.org_api.delete_org(org['name'])