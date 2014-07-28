'''
Created on Jul 28, 2014

@author: Daniel Gordon
'''
import unittest
import re

class Version(object):
    '''
    classdocs
    '''


    def __init__(self, version_str):
        '''
        Constructor
        '''
        if not re.match("^[\d.a-zA-Z]+$", version_str):
            raise NotImplementedError("That version string (%s) is not supported. Version should contain only Numbers, ., or rev letters (No spaces, -, :, _, etc...)." % version_str) 
        self.version_list = version_str.split(".")

        self.major = 0
        self.minor = 0
        self.build = 0
        if len(self.version_list) > 0:
            self.major = self.version_list[0]
        if len(self.version_list) > 1:
            self.minor = self.version_list[1]
        if len(self.version_list) > 2:
            self.build = self.version_list[2]
    
    def __cmp__(self, other):
        if not isinstance(other,Version):
            other = Version(other)
        
        for (ndx, other_val) in enumerate(other):
            if self[ndx] < other_val:
                return -1
            if self[ndx] > other_val:
                return 1

        return 0
    
    def __iter__(self):
        return iter(self.version_list)
    
    def __getitem__(self, at):
        #To ease checking, we just return 0 for any version part we don't have
        if len(self) > at:
            return self.version_list[at]
        else:
            return 0
    
    def __len__(self):
        return len(self.version_list)
    
    def __str__(self):
        return ".".join(self.version_list) 
    
    def to_tup(self):
        return tuple(self.version_list)
    
    
class TestVersion(unittest.TestCase):

    def setUp(self):
        self.vers_mmb = Version("1.2.3")
        self.vers_mmba = Version("1.2.3a")
        self.vers_long = Version("1.2.3.4.5")

    def test_equal(self):
        # check major, minor, build
        self.assertTrue(self.vers_mmb == "1.2.3", "Simple major, minor, build doesn't match!")
        self.assertTrue(self.vers_mmb != "1.2.4", "Simple major, minor, build matches something it shouldn't!")

    def test_greaterthan(self):        
        self.assertTrue(self.vers_mmb > "1.2.2", "Simple major, minor, build greater than test failed!")
        self.assertTrue(self.vers_mmb > "0.2.2", "Simple major, minor, build greater than test failed!")
        self.assertTrue(self.vers_mmb > "0.3.4", "Simple major, minor, build greater than test failed!")
        self.assertTrue(self.vers_mmb > "1.0", "Version with different number of version elements failed.")
        self.assertFalse(self.vers_mmb > "1.2.3.4", "Version with different number of version elements failed.")
        self.assertFalse(self.vers_mmb > "2.2.2", "Simple major, minor, build greater than test failed!")
        self.assertFalse(self.vers_mmb > "2.2", "Simple major, minor, build greater than test failed!")

    def test_lessthan(self):        
        self.assertTrue(self.vers_mmb < "1.2.4", "Simple major, minor, build less than test failed!")
        self.assertTrue(self.vers_mmb < "2.2.2", "Simple major, minor, build less than test failed!")
        self.assertTrue(self.vers_mmb < "2.3.4", "Simple major, minor, build less than test failed!")
        self.assertTrue(self.vers_mmb < "2.0", "Version with different number of version elements failed.")
        self.assertFalse(self.vers_mmb < "1.2", "Version with different number of version elements failed.")
        self.assertFalse(self.vers_mmb < "0.2.2", "Simple major, minor, build less than test failed!")

    def test_irregularstrings(self):        
        self.assertRaises(NotImplementedError, Version, "1.2.3 Rev:a")
        self.assertRaises(NotImplementedError, Version, "1.2.3_a")
        self.assertRaises(NotImplementedError, Version, "1.2.3_rc1")


if __name__ == '__main__':
    unittest.main()
