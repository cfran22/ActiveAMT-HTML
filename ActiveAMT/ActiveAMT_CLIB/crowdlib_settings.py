from crowdlib import settings as cls
import os


############################################################
# SERVICE TYPE
#
# This must be either "sandbox" or "production".
#
cls.service_type = "sandbox"


############################################################
# AWS ACCOUNT INFO
#
# You can find your AWS account ID and secret key here:
# https://console.aws.amazon.com/iam/home?#security_credential


# "Access Key ID" from AWS -- like a public key
cls.aws_account_id = "AKIAIW4DPZSUQKGPOMFA"

# "Secret Access Key" from AWS -- like a private key
cls.aws_account_key = "Wv0riAVviH2L/CceEnOMV5EoG5dgMUC13NloDLpz"



############################################################
# DATABASE LOCATION
#
# This is the directory where CrowdLib will store the SQLite database(s) that it
# needs to function.  It can be any directory.  It is best to point it to a
# central location so that all of your CrowdLib projects can share the same
# database.
#
cls.db_dir = os.path.expanduser("~/.crowdlib_data/")
# This will put it at $HOME/.crowdlib_data on UNIX,
# C:\Users\YourUserName\.crowdlib_data\ on Windows 7, and so on.


############################################################
# DEFAULT PARAMETERS
#
# When creating HITs, these will be used unless you specify
# other values explicitly.
#
cls.default_autopay_delay = 60*60*48 # Default: Automatically pay after 48 hours
cls.default_reward = 0.05            # Default: $0.05 per HIT
cls.default_lifetime = 60*60*24*7    # Default: HITs expire after 1 week
cls.default_max_assignments = 1      # Default: 1 judgment per HIT
cls.default_time_limit = 60*30       # Default: Treat HITs as abandoned after 30 mins
cls.default_qualification_requirements = () # Default: no qualification requirements
cls.default_requester_annotation = ""# Default: no requester annotation
cls.default_keywords = ()            # Default: no keywords

# Importable dictionary of all default values. Bring into project as hit_type, set what you want to set.
default_hittype = {"title": None, "description": None, "reward": cls.default_reward, "time_limit": cls.default_time_limit,
            "keywords": cls.default_keywords, "autopay_delay": cls.default_autopay_delay,
            "qualification_requirements": cls.default_qualification_requirements, "lifetime": cls.default_lifetime,
            "requester_annotation": cls.default_requester_annotation, "max_assignments": cls.default_max_assignments}
