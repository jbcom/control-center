const { Authenticator } = require('cognito-at-edge');

// Create the Authenticator with hardcoded configuration values
const authenticator = new Authenticator({
  region: '${region}',
  userPoolId: '${user_pool_id}',
  userPoolAppId: '${app_client_id}',
  userPoolAppSecret: '${app_client_secret}',
  userPoolDomain: '${cognito_domain}',
  cookieExpirationDays: 30,
  cookiePath: '/',
  cookieDomain: '${cookie_domain}',
  httpOnly: true,
  logLevel: 'none'
});

// Export the Lambda handler function
exports.handler = async (event) => {
  return authenticator.handleRefreshToken(event);
}; 