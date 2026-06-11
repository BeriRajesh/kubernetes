from getParameterSecrets import getCredentials
dsdk_username, dsdk_password  = getCredentials('dev.app.redshift.dsdk.user','dev.app.redshift.dsdk.pass')

print 'dsdk_password  =', dsdk_password
print 'dsdk_username  =', dsdk_username
