#!/usr/bin/env python3
"""Exercise failure boundaries with fake executables; not Jena integration tests."""
import os, subprocess, tempfile, unittest
from pathlib import Path
SCRIPT=Path('images/jena-tools/load.sh').resolve()
class Loader(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.bin=self.root/'bin'; self.bin.mkdir()
        self.log=self.root/'calls'
        for tool in ['riot','tdbloader','tdb2.tdbloader','java']:
            f=self.bin/tool
            f.write_text('#!/bin/sh\nprintf "%s\\n" "'+tool+' $*" >> "$CALLS"\ncase "'+tool+'" in riot) exit "${RIOT_EXIT:-0}";; tdb*) exit "${LOADER_EXIT:-0}";; esac\n')
            f.chmod(0o755)
        self.source=self.root/'dump.ttl'; self.source.write_text('')
        self.dest=self.root/'db'
        self.env={**os.environ,'PATH':str(self.bin)+':'+os.environ['PATH'],'CALLS':str(self.log),'STORAGE_ENGINE':'TDB1','BUILD_TEXT_INDEX':'false'}
    def run_load(self,*args):
        return subprocess.run(['sh',str(SCRIPT),*map(str,args)],env=self.env,capture_output=True,text=True)
    def test_validation_before_load(self):
        self.assertEqual(self.run_load(self.dest,self.source).returncode,0)
        self.assertEqual([s.split()[0] for s in self.log.read_text().splitlines()],['riot','tdbloader'])
        self.assertNotEqual(self.run_load(self.dest,self.source).returncode,0)
    def test_validation_failure(self):
        self.env['RIOT_EXIT']='23'
        self.assertEqual(self.run_load(self.dest,self.source).returncode,23)
        self.assertFalse(self.dest.exists())
    def test_loader_failure(self):
        self.env['LOADER_EXIT']='24'
        self.assertEqual(self.run_load(self.dest,self.source).returncode,24)
        self.assertTrue(self.dest.is_dir())
    def test_tdb2_and_arguments(self):
        self.env['STORAGE_ENGINE']='TDB2'
        self.assertEqual(self.run_load(self.dest,self.source).returncode,0)
        self.assertIn('tdb2.tdbloader',self.log.read_text())
        self.assertNotEqual(self.run_load().returncode,0)
    def test_version_mismatch(self):
        self.env.update(EXPECTED_JENA_VERSION='5.4.0',JENA_VERSION='5.5.0')
        self.assertNotEqual(self.run_load(self.dest,self.source).returncode,0)
        self.assertFalse(self.dest.exists())
    def test_symlink_refused(self):
        self.dest.symlink_to(self.root/'nonexistent')
        self.assertNotEqual(self.run_load(self.dest,self.source).returncode,0)
if __name__=='__main__':unittest.main()
