import copy, json, tempfile, unittest
from pathlib import Path
from exam_mastery.ingest import ingest
from exam_mastery.providers import Provider
from exam_mastery.workflow import run
from exam_mastery.validate import *
from exam_mastery.common import read_json,ContractError

ROOT=Path(__file__).resolve().parent.parent
FIX=ROOT/'fixtures'/'synthetic_responses'; SOURCES=ROOT/'fixtures'/'synthetic_course'

class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.manifest=ingest(SOURCES,Path(cls.tmp.name)/'manifest.json')
        cls.bp=read_json(FIX/'architect.json');cls.research=read_json(FIX/'research.json'); cls.author=read_json(FIX/'author.json')
        cls.assess=read_json(FIX/'assessment.json');cls.cards=read_json(FIX/'cards.json');cls.inter=read_json(FIX/'interaction.json');cls.design=read_json(FIX/'design.json')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_source_hashes_and_locators(self):
        self.assertEqual(len(self.manifest['sources']),1)
        self.assertEqual(len(self.manifest['sources'][0]['sha256']),64)
        self.assertTrue(self.manifest['chunks'][0]['locator'].endswith(':p1'))
    def test_valid_fixture(self):
        check_blueprint(self.bp,self.manifest);check_research(self.research,self.manifest);check_author(self.author,self.manifest)
        check_assess(self.assess,self.bp,self.manifest);check_cards(self.cards,self.bp,self.manifest)
        check_interaction(self.inter,self.bp);check_design(self.design)
    def test_open_world_reasoning_operation(self):
        bp=copy.deepcopy(self.bp)
        bp['competencies'][0]['operation']='subsume'
        check_blueprint(bp,self.manifest) # no fixed domain enumeration
    def test_missing_source_ref_blocks(self):
        bp=copy.deepcopy(self.bp);bp['competencies'][0]['source_refs']=['fake:p900']
        with self.assertRaises(ContractError):check_blueprint(bp,self.manifest)
    def test_false_coverage_blocks(self):
        ass=copy.deepcopy(self.assess);ass['items'][0]['required_operations']=['compare']
        with self.assertRaises(ContractError):check_assess(ass,self.bp,self.manifest)
    def test_rubric_sum_blocks(self):
        ass=copy.deepcopy(self.assess);ass['items'][0]['rubric'][0]['points']=44
        with self.assertRaises(ContractError):check_assess(ass,self.bp,self.manifest)
    def test_no_transfer_blocks(self):
        ass=copy.deepcopy(self.assess);ass['items'][-1]['difficulty']='independent'
        with self.assertRaises(ContractError):check_assess(ass,self.bp,self.manifest)
    def test_duplicate_cards_block(self):
        cards=copy.deepcopy(self.cards);cards['cards'][1]['question']=cards['cards'][0]['question']
        with self.assertRaises(ContractError):check_cards(cards,self.bp,self.manifest)
    def test_short_exact_answer_allowed_with_explanation(self):
        cards=copy.deepcopy(self.cards);cards['cards'][0]['answer']='No.'
        check_cards(cards,self.bp,self.manifest)
    def test_empty_answer_still_blocks(self):
        cards=copy.deepcopy(self.cards);cards['cards'][0]['answer']=' '
        with self.assertRaises(ContractError):check_cards(cards,self.bp,self.manifest)
    def test_numeric_reference_blocks(self):
        inter=copy.deepcopy(self.inter);inter['numeric']['reference_at_default']=99
        with self.assertRaises(ContractError):check_interaction(inter,self.bp)
    def test_injection_expression_blocks(self):
        inter=copy.deepcopy(self.inter);inter['numeric']['expression']='__import__("os").system("whoami")'
        with self.assertRaises(ContractError):check_interaction(inter,self.bp)
    def test_numeric_endpoints_finite(self):
        inter=copy.deepcopy(self.inter);inter['numeric']['expression']='1/(tax-tax)'
        with self.assertRaises(ZeroDivisionError):check_interaction(inter,self.bp)
    def test_audit_self_contradiction_blocks(self):
        audit=read_json(FIX/'audit.json');audit['unverified_claims']=['K1']
        with self.assertRaises(ContractError):check_audit(audit,self.bp)
    def test_full_pipeline_draft_not_release(self):
        with tempfile.TemporaryDirectory() as dest:
            status=run(SOURCES,Path(dest)/'run',Provider('fixture'),Provider('fixture'),fixture_dir=FIX)
            self.assertEqual(status['status'],'NEEDS_REVIEW')
            pkg=Path(dest)/'run'/'artifacts'
            self.assertTrue((pkg/'learning_package.pdf').stat().st_size>8000)
            self.assertTrue((pkg/'web'/'index.html').stat().st_size>3000)
            data=(pkg/'anki'/'anki_import.tsv').read_text(encoding='utf-8')
            self.assertEqual(data.count('\n')-3,len(self.cards['cards']))
            self.assertIn('#columns:ID',data)
    def test_long_title_reflows_at_320_pixels(self):
        import importlib.util
        if not importlib.util.find_spec('playwright'):self.skipTest('Chromium QA unavailable')
        from playwright.sync_api import sync_playwright
        from exam_mastery.publish import publish_html
        bp=copy.deepcopy(self.bp);bp['title']='Synthetic Development Material: Implication, Counterexamples, and Osmosis-Model Inference'
        with tempfile.TemporaryDirectory() as d:
            path=publish_html(bp,self.author,self.assess,self.cards,self.inter,self.design,Path(d))
            with sync_playwright() as p:
                browser=p.chromium.launch();page=browser.new_page(viewport={'width':320,'height':800});page.goto(path.as_uri())
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                browser.close()
    def test_no_lab_has_no_broken_navigation(self):
        from exam_mastery.publish import publish_html
        with tempfile.TemporaryDirectory() as d:
            inter={'kind':'none','reason':'No relevant interactive mechanism','competency_ids':[]}
            path=publish_html(self.bp,self.author,self.assess,self.cards,inter,self.design,Path(d))
            self.assertNotIn('href="#lab"',path.read_text())
    def test_inaccessible_design_blocks(self):
        d=copy.deepcopy(self.design);d['theme']['accent']='#fffffe'
        with self.assertRaises(ContractError):check_design(d)
    def test_no_sources_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ContractError):ingest(Path(d),Path(d)/'out.json')

if __name__=='__main__':unittest.main()
