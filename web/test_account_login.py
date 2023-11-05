import re

from tests.support import fixtures
fixtures.global_setup()

from unittest import TestCase
from unittest.mock import MagicMock

import requests
from http import cookiejar
from html import unescape

from resources.lib import ipwww_common

import credentials
from resources.lib import ipwww_common
from tests.support.testutils import doc_path

# setUpModule = fixtures.setup_web_test()



class SignIn(TestCase):
    def signin_by_web(self):
        """
        Not intended to be run as test.
        Just some information obtained by following HTTP streams of an account sing in using Firefox.
        The calls like requests.get(...) are the requests made by the webbrowser and the comments show
        additional info regarding the request and the response.

        The sing-in procedure at BBC iplayer comes down to
            1.  Client requests a page at ...bbc.co.uk which requires authentication
            2.  Server redirects to session.bbc.co.uk/session, with url to the original page as data in the query string
            4.  Client requests session
            5.  Server redirects to account.bbc.com/auth, set a ckns_nonce for domain .bbc.co.uk and adds quite a lot
                of info in the query string, including the original url and a nonce
            6.  Client requests auth
            7.  Server returns the login page, requesting the user's username.
            8.  Client obtains the response url from the page, which include a nonce (different from 5.), a sequence ID
                and the original url in the querystring. Client posts username to that url, which is auth/username.
            9.  Server responds with OK and basically the same page, now requesting the password.
            10. Client now posts both username and password to auth/password. The querystring is the same as in 8,
                including the sequence ID.
            11. Server redirects back to session.bbc.co.uk/session and set cookies ckns_session and ckns_jwt on
                domain .account.bbc.com. Again with a querystring containing some account related info, the orignal
                url, etc.
            12. Client requests session with the ckns_nonce cookie obtained from step 5.
            13. Server redirects to original page and set the cookies: ckns_rtkn, ckns_sylphid, ckpf_sylphid, ckns_id,
                ckns_atkn and ckns_idtkn on domain .bbc.co.uk
        """

        requests.get('https://session.bbc.co.uk/session?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching&context=iplayer&userOrigin=iplayer')
        # Query:    ptrt:       https://www.bbc.co.uk/iplayer/watching
        #           context:    iplayer
        #           userOrigin: iplayer
        # Sends cookie:  ckns_mvt=2bf45209-3689-4349-a53b-4f9b9c7847fb
        #               ckns_explicit=0
        #               ckns_policy=000
        #               ckns_privacy=july2019
        #               ckns_iplayer_experiments={}
        #               ckns_policy_exp=1729962489995
        #               atuserid=%7B%22name%22%3A%22atuserid%22%2C%22val%22%3A%220edf5c47-8b72-4465-935d-d0f8fb9d4ec3%22%2C%22options%22%3A%7B%22end%22%3A%222024-11-26T17%3A08%3A09.997Z%22%2C%22path%22%3A%22%2F%22%7D%7D
        #
        # Returns 302 Found, content-type text/html, redirects to account.bbc.com
        # Sets cookies: ckns_nonce=oaImjBEjKpjXyBMz1XY_04A3; Domain=.bbc.co.uk; Path=/; HttpOnly; Secure; SameSite=None
        #
        # small html -like content:
        # <p>
        #   Found. Redirecting to
        #   <a href="https://account.bbc.com/auth?realm=%2F&amp;clientId=Account&amp;context=iplayer&amp;ptrt=https%3A%2F%2Fwww.bb
        # c.co.uk%2Fiplayer%2Fwatching&amp;userOrigin=iplayer&amp;isCasso=false&amp;action=sign-in&amp;redirectUri=https%3A%2F%2Fs
        # ession.bbc.co.uk%2Fsession%2Fcallback%3Frealm%3D%2F&amp;service=IdSignInService&amp;nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI
        # 3JIKGQ">https://account.bbc.com/auth?realm=%2F&amp;clientId=Account&amp;context=iplayer&amp;ptrt=https%3A%2F%2Fwww.bbc.c
        # o.uk%2Fiplayer%2Fwatching&amp;userOrigin=iplayer&amp;isCasso=false&amp;action=sign-in&amp;redirectUri=https%3A%2F%2Fsess
        # ion.bbc.co.uk%2Fsession%2Fcallback%3Frealm%3D%2F&amp;service=IdSignInService&amp;nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JI
        # KGQ</a>
        # </p>

        # Full url and querystring from redirect location:
        requests.get('https://account.bbc.com/auth?realm=%2F&clientId=Account&context=iplayer&ptrt=https%3A%2F%2F' 
                     'www.bbc.co.uk%2Fiplayer%2Fwatching&userOrigin=iplayer&isCasso=false&action=sign-in&redirectUri=' 
                     'https%3A%2F%2Fsession.bbc.co.uk%2Fsession%2Fcallback%3Frealm%3D%2F&service=IdSignInService' 
                     '&nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ')
        # Query:    realm:       /
        #           clientId:    Account
        #           context:     iplayer
        #           ptrt:        https://www.bbc.co.uk/iplayer/watching
        #           userOrigin:  iplayer
        #           isCasso:     false
        #           action:      sign-in
        #           redirectUri: https://session.bbc.co.uk/session/callback?realm=/
        #           service:     IdSignInService
        #           nonce:       c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ
        # No cookies send
        #
        # Returns 200 - OK, content-type text/html
        # Set cookies:  ckns_mvt=dd00d9e3-36b7-4ac1-95e7-e00330d88166; Domain=.account.bbc.com
        #
        # Full HTML page requesting to enter username (not password)

        # post username            !****** IMPORTANT: Probably sent without VPN ******!
        #       URL obtained from a request that had been sent over VPN
        requests.post('https://account.bbc.com/auth?action=sign-in&clientId=Account&context=iplayer&isCasso=false&' 
                     'nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ&ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2F'
                     'watching&realm=%2F&redirectUri=https%3A%2F%2Fsession.bbc.co.uk%2Fsession%2Fcallback%3Frealm%3D'
                     '%2F&sequenceId=b139c1d2-d556-4648-821d-242a9c51502d&service=IdSignInService&userOrigin=iplayer')
        # Query:    realm=/
        #           clientId = Account
        #           context=iplayer
        #           ptrt=https://www.bbc.co.uk/iplayer/watching
        #           userOrigin=iplayer
        #           isCasso=false
        #           action=sign-in
        #           redirectUri=https://session.bbc.co.uk/session/callback?realm=/
        #           service=IdSignInService
        #           nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ
        #           sequenceId=b139c1d2-d556-4648-821d-242a9c51502d
        # url encoded form:
        #       username: <my username>
        # Sends cookies:    ckns_mvt=dd00d9e3-36b7-4ac1-95e7-e00330d88166
        #                   atuserid=%7B%22name%22%3A%22atuserid%22%2C%22val%22%3A%224e90640d-2344-4c5d-82d9-6d007b383d1b%22%2C%22options%22%3A%7B%22end%22%3A%222024-11-26T17%3A08%3A30.628Z%22%2C%22path%22%3A%22%2F%22%7D%7D

        # Returns 200 - OK, content-type text/html
        # No cookies set
        # Full HTML page requesting password

        requests.get('https://idcta.api.bbc.co.uk/idcta/config?callback=&ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching HTTP/2.0 ')
        # Querry:   callback:
        #           ptrt:     https://www.bbc.co.uk/iplayer/watching
        # No cookies send
        #
        # Return 200 -OK, content-type text/javascript
        # Sets no cookies
        # Body is basically a datastructure almost conform json.
        #/**/
        """
typeof define === 'function' && define( {
"accessTokenUrl":"https://account.bbc.com/external/v3/user/access_token",
"announce_url":"https://session.bbc.co.uk/session/announce",
"bbcid-v5":"GREEN",
"child_parent_linking_url":"https://account.bbc.com/account/settings/linked-accounts",
"id-availability":"GREEN",
"account-maintenance-mode":"off",
"foryou-access-chance":"25",
"foryou-flagpole":"GREEN",
"identity": {
    "accessTokenCookieName":"ckns_atkn",
    "cookieAgeDays":730,
    "idSignedInCookieName":"ckns_id"
  },
"identityTokenExchangeUrl":"https://session.bbc.co.uk/session/token-exchange",
"nma": {
    "refresh_url":"https://session.bbc.co.uk/session/tokens",
    "register_url":"https://session.bbc.co.uk/session?action=re gister&ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
           "signin_url":"https://session.bbc.co.uk/session?ptrt=https %3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
    "signout_url":"https://session.bbc.co.uk/session/nma-signout",
    "user_details _url":"https://session.bbc.co.uk/session/user-details"
  },
"experiments": {
    "usi":"17665700397",
    "usiApiName":"8435701282_url_targeting_for_accxp_usi_msi"
  },
"federated": {
    "authoriseUrl":"https://account.bbc.com/signin/federated/authorise?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
    "callbackUrl":"https://session.bbc.co.uk/session/callback/federated",
    "signInUrl":"https://account.bbc.com/signin/federated?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
    "registerUrl":"https://account.bbc.com/register/federated?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching"
  },
"features": {
    "showUsiModal":false,
    "clientAnalytics":false,
    "webCoreUsiModal":true,
    "removeJsTruncation":true
},
"forYouAllowlist":["C2pJ5M4xyS0MNNOpzzJVAr_RWVwqbXVleGcZbUYrkEk","bRfoYQF0vCQpsCV_l3Fv5sQpw8iYLmKTskLCR25LFZQ",
                   "nC7MiQzxDgcBN-iMbVX7uxBUGE01NMDJPE6coiCUft0","A764DYgdG4U7r5q6gJgXxbVcoznQi0MkPt0_-0V9Qgg",
                   "MgLVCfbcC0pWSh-XmP8yeqy4h4IR8IBjcIPRCYC0ERc","T2j1jevJaoCEmJj37afB6XOUbcfy9WE-4kBcLEkjagI",
                   "h1L8inzcJhfWPlkdrCgJPtCg6ViwNEduD64GDZKjJDc","MVSDy1g9CTu-3tfp5O4pnIO4a-dF890Nv-BbbiMecV0",
                   "lQcdMbgKlLNfBU2ewdLeLZlyMpinNfwwMbescwp-V7Y","EhgrGOWloM4gYSlAK1yW674__NCvSBC-NfxvF0vLqzc",
                   "c85NPNqVeb801ETDymQ0uRrjJVVHWfGoN_E-XnIXqHY","3Y7iRWtByUgA28giNdYONKHHRdbCcDrNLoXTp2iRqP4",
                   "FqgTVk7syqF_xnM5JfBuc8B2df-AKkR6xrDMEFLsRVY","fN0cRRWQNqFMOsPtOXerlaEK2MlzDGc76c2KhgshHvQ",
                   "jM7db8snxPsnwrLqQgC7GnKIzcZszJdHRkkOhpWNssE","o4mIVwM
6pLEntPNKPVzQzyC5mYVyyxoO6nkW9d8yxR0","YBrLpe07lOqPJKcLTAcm1fSPP-ng4wp9gGPjcrWlWj4","0uQI2zfpHc5Y8ypdVZcrXJPf0kCnGo114Gd
nSVq0zXA","JRs0GAC3P70-9_gFrzwvCo7cfLVKnW3ZyvYVqrVKUl8","VMEOmh3fCoaZosNGdbkuuNt1vl1lvGvLbU27GKvmG1M","lZ5hh6Y09u_nGv-qw
hMDQJ0LraA1G1IQrjvK9k64HX0","nVgyLP4ZYfH5R2QdnY0duPse0py2p99Jvn_uruTNeKw","ykeqelE2OVWcgPXjDULCb8u4CrBGekBV69OHVYqK9o4",
"Nxmg5asPWpSUpmO93sF3n2f8V3V-oWDe15ddh-tCNxQ","strZYISnor3v2vKD9K2oGMEysK3j8TZK2rF8li71rdQ","ZPfuHwze9jWp7WlEgd7lU7iJvn3
5jSSRT42BsAMN3sk","R09O6N5oFUnusoUOodSoaawQ-ww7IItzD9mqBREOZwA","n_yvX5-p4w-qHalpMm_Tgezjh5I-P_LnJEZHnJhxCC0","BF1qcLFbZ
EZr_dF1knJxoj9CekS3rU6mf8mVyHS6Akk","05KuXlU9y2Cw8d1TaB6D7RkOJq-ttrg8vQHLCWLY4ys","_8sSpqGZ_y_zNJ4WStaKKOoxkzWP4bVbTALEQ
qan4VM","uBdh0OLJOusGu6JzjzZuhF2CzMGE7tmG7LaFlSe26xA","DMJLZw54ZaSxhDHVWbAPOsFhFLIXI6dwm8opYCyb3lw","Am6frwvJ-s65mwDEx7J
2TqIO0538A7Zcy9zosyjp-lE","stMxS_lr1PKSOsbvSD-S6tz-gyc5k1tElukfdlt3swA","6gjwrtO6uVE3nvytIPZEMcJCQNGNsBLOyyglI2Up0sQ","E
oj6Wd6Q53KPrdaaFTCDHPM9HbFIgGO3ayZiPNErTeQ","VRrJBPaA1HaI5F4qR95EsYm6nP70_oRSeB_qP7rvToA","5Z0y2rKFhvoM10zmTF_cK82GvgQk2
HBkORyK7VVb7lk","Z-QJ98yKMGGkhlUKR0Jf-cu30OtRbxXEv4YIUe_EOZ8","TFIegHZt969_qkt7Yi2Ou2-zkkchei5ELJ1FAzaXwYs","4baFnfjyXh5
Dz9ssx8xwatda9VcdA5WEiBcn-H5gfT0","V2KyZQjoChU0yczYPQLr1zcKzdvJClyQxWZf5R9YGtc","mWSWHcS3kt2Z-X6wlJ1l-pf11nRd3HTj43TlvLU
c8pI","lBgntIDMCr-UxNWq0hoCzMJMzjv8sPSoiFgAYoeLtUo","0B2ICp1QaT2v89YszUASAJ14Qx9vaUn_hXpKJDKZN1M","sc2ibgIQlzwKjzOBVdpZQ
CyY8HonVPpfT6QPYCOhWtI","-6bl3aOXj-O8isoCQBLNsxk7tB_n2mL9mYQuY1ySeOQ","iCHjlGbIg77ioutf1l-Wf28Rlcm_1Pr84G0Y_ihotUU","UmE
2savN8YGVg4YA_IfL5Hlo9lhv1kRxFVOt1XnS_6M","7kl7l0sAVdgEZVRVCyQzlsDqPIoquy4XPDg1s6F33h8","MgwgIR1uvI4v7ogliftc7MR3-vii3yR
cqAYKeN317Sg","x4YO99idK9Iu7grHwBJruYthaGUXC-52m-OOn4neQyA","23P8nA2cUQajSFEZuXCjPfVIf2ufrlf02Z07u6X1VlU","MlreTo299YEnu
SdLksvQ67RykBe89kClPUQ4jT5QzNc","91IN1EEWaChSJybrvWSaeTyAxPrJafzsfWcifVsr4DE","GbH4cLy2wXAdEql9mj3-1IwXtb-qV_4IHETs3fGhH
8g"],
"privacy_settings_url":"https://account.bbc.com/account/settings/privacy",
"profiles": {
    "list":"https://session.bbc.co.uk/session/profiles",
    "create":"https://account.bbc.com/register/details/profile?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
    "picker":"https://session.bbc.com/session/tokens/profile-admin?switchTld=0&ptrt=https%3A%2F%2Faccount.bbc.com%2Faccount%2Fprofile-picker%3Fptrt%3Dhttps%253A%252F%252Fwww.bbc.co.uk%252Fiplayer%252Fwatching"
  },
"register_url":"https://session.bbc.co.uk/session?action=register&ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"settings_url":"https://account.bbc.com/account/settings?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"signin_url":"https://session.bbc.co.uk/session?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"signout_url":"https: //account.bbc.com/signout?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"status_url":"https://account.bbc.com/account?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"foryou_url":"https://www.bbc.com/foryou?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"tokenImprovement":"GREEN",
"tokenRefresh":true,
"tokenRefresh_signout_url":"https://session.bbc.co.uk/session/signout?switchTld=true&ptrt=https%3A%2F%2Faccount.bbc.com%2Fsignout%3Fptrt%3Dhttps%253A%252F%252Fwww.bbc.co.uk%252Fiplayer%252Fwatching",
"tokenRefresh_url":"https://session.bbc.co.uk/session?ptrt=https%3A%2F%2Fsession.bbc.co.uk%2Fsession%2Fannounce",
"tokenUrl":"https://account.bbc.com/external/v3/user/token",
"usiDestinationWhitelist":["homepage_ps","news_ps","sport_ps","account"],
"translations": {
    "statusbarSignedIn":"Your account",
    "statusbarSignedOut":"Sign in",
    "statusbarForYou":"For you"
  },
"unavailable_url":"https://account.bbc.com/account/error?ptrt=https%3A%2F%2Fwww.bbc.co.uk%2Fiplayer%2Fwatching",
"web":
{
    "callbackUrl":"https://session.bbc.co.uk/session/callback",
    "credentialsUrl":"https://account.bbc.com/signin"
}
}
);
"""
        # Post password   !****** IMPORTANT: Probably sent without VPN ******!
        requests.post('https://account.bbc.com/auth/password?action=sign-in&clientId=Account&context=international' 
                      '&isCasso=false&nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ&ptrt=https%3A%2F%2Fwww.bbc.co.uk%2F'
                      'iplayer%2Fwatching&realm=%2F&redirectUri=https%3A%2F%2Fsession.bbc.co.uk%2Fsession%2Fcallback%3F'
                      'realm%3D%2F&sequenceId=b139c1d2-d556-4648-821d-242a9c51502d&service=IdSignInService&' 
                      'userOrigin=iplayer')
        # Query:    realm=/
        #           clientId=Account
        #           context=international       <= Due to missing VPN???
        #           ptrt=https://www.bbc.co.uk/iplayer/watching
        #           userOrigin=iplayer
        #           isCasso=false
        #           action=sign-in
        #           redirectUri=https://session.bbc.co.uk/session/callback?Frealm=/
        #           service=IdSignInService
        #           nonce=c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ
        #           sequenceId=b139c1d2-d556-4648-821d-242a9c51502d     <= same ID as sending username
        # URLencoded Form (in plain text):
        #       username: <my username>
        #       password: <my password>
        # Send cookie:  ckns_mvt=dd00d9e3-36b7-4ac1-95e7-e00330d88166
        #               atuserid=%7B%22name%22%3A%22atuserid%22%2C%22val%22%3A%224e90640d-2344-4c5d-82d9-6d007b383d1b%22%2C%22options%22%3A%7B%22end%22%3A%222024-11-26T20%3A15%3A42.396Z%22%2C%22path%22%3A%22%2F%22%7D%7D
        #
        # Returns 302 - Found, redirects to session.bbc.co.uk
        # Sets cookies: ckns_session;   Domain=.account.bbc.com
        #               ckns_jwt;       Domain=.account.bbc.com

        requests.get('https://session.bbc.co.uk/session/callback?realm=/&code=2hdr9VE1bR-SyqmlCMgiNeCUSJo&iss=https%3A'
                     '%2F%2Faccess.api.bbc.com%2Fbbcidv5%2Foauth2&state=%7B%22action%22%3A%22sign-in%22%2C%22clientId%22'
                     '%3A%22Account%22%2C%22context%22%3A%22international%22%2C%22isCasso%22%3A%22false%22%2C%22nonce'
                     '%22%3A%22c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ%22%2C%22ptrt%22%3A%22https%3A%2F%2Fwww.bbc.co.uk%2F'
                     'iplayer%2Fwatching%22%2C%22realm%22%3A%22%2F%22%2C%22redirectUri%22%3A%22https%3A%2F%2F'
                     'session.bbc.co.uk%2Fsession%2Fcallback%3Frealm%3D%2F%22%2C%22service%22%3A%22IdSignInService%22'
                     '%2C%22userOrigin%22%3A%22iplayer%22%7D&client_id=Account')
        # Query:    realm:     /
        #           code:      2hdr9VE1bR-SyqmlCMgiNeCUSJo
        #           iss:       https://access.api.bbc.com/bbcidv5/oauth2
        #           state:     {"action":"sign-in","clientId":"Account","context":"international","isCasso":"false",
        #                       "nonce":"c7XUQm29-kKRcAfyNX1OhiLBPpEPxI3JIKGQ",
        #                       "ptrt":"https://www.bbc.co.uk/iplayer/watching","realm":"/",
        #                       "redirectUri":"https://session.bbc.co.uk/session/callback?realm=/",
        #                       "service":"IdSignInService","userOrigin":"iplayer"}
        #           client_id: Account
        # Sends cookies: ckns_mvt=2bf45209-3689-4349-a53b-4f9b9c7847fb
        #                ckns_explicit=0
        #                ckns_policy=000
        #                ckns_privacy=july2019
        #                ckns_iplayer_experiments={}
        #                ckns_policy_exp=1729962489995
        #                ckns_nonce=oaImjBEjKpjXyBMz1XY_04A3       <-- is the nonce cookie set in the response to the
        #                                                              first request
        #
        # Returns 302 - Found, redirects to www.bbc.co.uk/iplayer/watching  <-- !!!!!!
        # Sets cookies: ckns_rtkn;      Domain=.session.bbc.co.uk  <-- Refresh token??
        #               ckns_sylphid;   Domain=.bbc.co.uk
        #               ckpf_sylphid;   Domain=.bbc.co.uk
        #               ckns_id;        Domain=.bbc.co.uk
        #               ckns_atkn;      Domain=.bbc.co.uk
        #               ckns_idtkn;     Domain=.bbc.co.uk


    def test_sign_in_co_uk(self):
        resp = requests.get('https://session.bbc.co.uk/session',
                            # This defines basically the page that initiated sign in, so
                            # after successful sign in we are redirected to this page.
                            # Without it were are redirected to the main page, i.e. https://www.bbc.co.uk
                            # params={'ptrt': 'https://www.bbc.co.uk/iplayer/watching',
                            #         'context': 'iplayer',
                            #         'userOrigin': 'iplayer'},
                            allow_redirects=False)
        self.assertEqual(302, resp.status_code)
        self.assertTrue('ckns_nonce' in resp.cookies)
        # This cookie is only set when the request has been done without the params.
        self.assertTrue('ckns_id-session-redirects' in resp.cookies)
        self.assertEqual(2, len(resp.cookies))
        new_url = resp.headers['location']
        self.assertTrue(new_url.startswith('https://account.bbc.com'))
        session_cookies = resp.cookies

        resp = requests.get(new_url)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        self.assertTrue('ckns_mvt' in resp.cookies)
        self.assertEqual(1, len(resp.cookies))
        # from iplayer WWW addon:
        match = re.search('action="([^"]+)"', resp.text)
        new_path = match[1]
        self.assertTrue(new_path.startswith('/auth?'))
        account_cookies = resp.cookies

        # Strip path from the query string of `new_path` and build a new urld
        url = 'https://account.bbc.com/auth/password' + unescape(new_path[5:])
        resp = requests.post(url,
                             headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',
                                       'Origin': 'https://account.bbc.com'},
                             data={'username': credentials.uname,
                                   'password': credentials.passw},
                             cookies=account_cookies,
                             allow_redirects=False)
        self.assertEqual(302, resp.status_code)
        self.assertTrue('ckns_session' in resp.cookies)
        self.assertTrue('ckns_jwt' in resp.cookies)
        self.assertEqual(2, len(resp.cookies))
        # check that a successful auth redirects to the session again, which will in turn set cookies
        # and redirect to the original page.
        new_url = resp.headers['location']
        self.assertTrue(new_url.startswith('https://session.bbc.co.uk/session/callback?'))
        self.assertTrue('state=["' in new_url)
        self.assertTrue('code=' in new_url)

        resp = requests.get(new_url,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'},
                            cookies=session_cookies,
                            allow_redirects=False)
        self.assertEqual(302, resp.status_code)
        self.assertTrue(resp.headers['location'].startswith('https://www.bbc.co.uk'))
        self.assertTrue('ckns_rtkn' in resp.cookies)
        self.assertTrue('ckns_sylphid' in resp.cookies)
        self.assertTrue('ckpf_sylphid' in resp.cookies)
        self.assertTrue('ckns_id' in resp.cookies)
        self.assertTrue('ckns_atkn' in resp.cookies)            # <- == access token
        self.assertTrue('ckns_idtkn' in resp.cookies)
        # check no other cookies were set
        self.assertEqual(6, len(resp.cookies))

    def test_sign_in_com(self):
        resp = requests.get('https://session.bbc.com/session',
                            # This defines basically the page that initiated sign in, so
                            # after successful sign in we are redirected to this page.
                            # Without it were are redirected to the main page, i.e. https://www.bbc.co.uk
                            # params={'ptrt': 'https://www.bbc.co.uk/iplayer/watching',
                            #         'context': 'iplayer',
                            #         'userOrigin': 'iplayer'},
                            allow_redirects=False)
        self.assertEqual(302, resp.status_code)
        self.assertTrue('ckns_nonce' in resp.cookies)
        # This cookie is only set when the request has been done without the params.
        self.assertTrue('ckns_id-session-redirects' in resp.cookies)
        self.assertEqual(2, len(resp.cookies))
        new_url = resp.headers['location']
        self.assertTrue(new_url.startswith('https://account.bbc.com'))
        session_cookies = resp.cookies

        resp = requests.get(new_url)
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
        self.assertTrue('ckns_mvt' in resp.cookies)
        self.assertEqual(1, len(resp.cookies))
        # from iplayer WWW addon:
        match = re.search('action="([^"]+)"', resp.text)
        new_path = match[1]
        self.assertTrue(new_path.startswith('/auth?'))
        account_cookies = resp.cookies

        # Strip path from the query string of `new_path` and build a new urld
        url = 'https://account.bbc.com/auth/password' + unescape(new_path[5:])
        resp = requests.post(url,
                             headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',
                                       'Origin': 'https://account.bbc.com'},
                             data={'username': credentials.uname,
                                   'password': credentials.passw},
                             cookies=account_cookies,
                             allow_redirects=False)
        self.assertEqual(302, resp.status_code)

        self.assertTrue('ckns_session' in resp.cookies)
        self.assertTrue('ckns_jwt' in resp.cookies)
        self.assertEqual(2, len(resp.cookies))
        # check that a successful auth redirects to the session again, which will in turn set cookies
        # and redirect to the original page.
        new_url = resp.headers['location']
        self.assertTrue(new_url.startswith('https://session.bbc.com/session/callback?'))
        self.assertTrue('state=["' in new_url)
        self.assertTrue('code=' in new_url)

        resp = requests.get(new_url,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'},
                            cookies=session_cookies,
                            allow_redirects=False)
        self.assertEqual(302, resp.status_code)
        self.assertTrue(resp.headers['location'].startswith('https://www.bbc.com'))
        self.assertTrue('ckns_rtkn' in resp.cookies)
        self.assertTrue('ckns_sylphid' in resp.cookies)
        self.assertTrue('ckpf_sylphid' in resp.cookies)
        self.assertTrue('ckns_id' in resp.cookies)
        self.assertTrue('ckns_atkn' in resp.cookies)            # <- == access token
        self.assertTrue('ckns_idtkn' in resp.cookies)
        # check no other cookies were set
        self.assertEqual(6, len(resp.cookies))

    def test_login_on_dot_com_after_co_dot_uk(self):
        p = re.compile('action="([^"]+)"')
        post_data = {
            'username': credentials.uname,
            'password': credentials.passw}

        with requests.session() as s:
            s.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'}
            resp = s.get('https://session.bbc.co.uk/session')
            match = p.search(resp.text)
            url = 'https://account.bbc.com/auth/password' + unescape(match[1][5:])
            resp = s.post(url,
                          headers={'Origin': 'https://account.bbc.com'},
                          data=post_data,
                          allow_redirects=False)
            resp = s.get(resp.headers['location'], allow_redirects=False)
            # Check authentication succeeded.
            self.assertTrue('ckns_atkn' in s.cookies)

            # Now authenticate on bbc.com
            resp = s.get('https://session.bbc.com/session', allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://account.bbc.com'))

            resp = s.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            new_url = resp.headers['location']
            # With the cookies for account.bbc.com we get redirected to session without having to provide credentials.
            self.assertTrue(new_url.startswith('https://session.bbc.com/session'))
            self.assertTrue('ckns_session' in resp.cookies)

            resp = s.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            # Redirected to bbc.co.uk, instead of bbc.com
            self.assertTrue(resp.headers['location'].startswith('https://www.bbc.co.uk'))
            self.assertTrue('ckns_rtkn' in resp.cookies)
            self.assertTrue('ckns_sylphid' in resp.cookies)
            self.assertTrue('ckpf_sylphid' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_atkn' in resp.cookies)  # <- == access token
            self.assertTrue('ckns_idtkn' in resp.cookies)
            # check no other cookies were set
            self.assertEqual(6, len(resp.cookies))

    def test_failed_sign_in_co_uk(self):
        resp = requests.get('https://session.bbc.co.uk/session',
                            allow_redirects=False)
        new_url = resp.headers['location']
        session_cookies = resp.cookies

        resp = requests.get(new_url)
        # from iplayer WWW addon:
        match = re.search('action="([^"]+)"', resp.text)
        new_path = match[1]
        account_cookies = resp.cookies

        # Strip path from the query string of `new_path` and build a new urld
        url = 'https://account.bbc.com/auth/password' + unescape(new_path[5:])
        resp = requests.post(url,
                             headers= {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',
                                       'Origin': 'https://account.bbc.com'},
                             data={'username': credentials.uname,
                                   'password': 'cfvsfdzv'},
                             cookies=account_cookies,
                             allow_redirects=False)
        self.assertEqual(200, resp.status_code)

    def test_signin_directly_on_account_auth(self):
        resp = requests.get('https://account.bbc.com/signin',
                            # This defines basically the page that initiated sign in, so
                            # after successful sign in we are redirected to this page.
                            # Without it were are redirected to the main page, i.e. https://www.bbc.co.uk
                            # params={'ptrt': 'https://www.bbc.co.uk/iplayer/watching',
                            #         'context': 'iplayer',
                            #         'userOrigin': 'iplayer'},
                            allow_redirects=False)
        self.assertTrue(resp.is_redirect)
        self.assertTrue(resp.headers['location'].startswith('https://session.bbc.co.uk/session'))

    def test_signin_on_account(self):
        with requests.Session() as session:
            session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'},
            resp = session.get('https://account.bbc.com/account', allow_redirects=False)
            self.assertTrue(resp.is_redirect)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.com/session?'))

            resp = session.get(new_url, allow_redirects=False)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://account.bbc.com/auth'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertFalse(resp.is_redirect)
            self.assertEqual('text/html; charset=utf-8', resp.headers['content-type'])
            self.assertTrue('ckns_mvt' in resp.cookies)
            self.assertEqual(1, len(resp.cookies))
            # from iplayer WWW addon:
            match = re.search('action="([^"]+)"', resp.text)
            new_path = match[1]
            self.assertTrue(new_path.startswith('/auth?'))

            # Strip path from the query string of `new_path` and build a new url to post username and password.
            url = 'https://account.bbc.com/auth/password' + unescape(new_path[5:])
            resp = session.post(url,
                                data={'username': credentials.uname,
                                    'password': credentials.passw},
                                allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_session' in resp.cookies)
            self.assertTrue('ckns_jwt' in resp.cookies)
            self.assertEqual(2, len(resp.cookies))
            self.assertFalse('state=["' in new_url)     # not very important, just to note that it's different to login from session.
            self.assertFalse('code=' in new_url)
            # check that a successful auth redirects to the session again, which will in turn set cookies
            # and redirect to the original page.
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.com/session/callback?'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_rtkn' in resp.cookies)
            self.assertTrue('ckns_sylphid' in resp.cookies)
            self.assertTrue('ckpf_sylphid' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_atkn' in resp.cookies)            # <- == access token
            self.assertTrue('ckns_idtkn' in resp.cookies)
            # check no other cookies were set
            self.assertEqual(6, len(resp.cookies))
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.co.uk/session'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_rtkn' in resp.cookies)
            self.assertTrue('ckns_sylphid' in resp.cookies)
            self.assertTrue('ckpf_sylphid' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_atkn' in resp.cookies)            # <- == access token
            self.assertTrue('ckns_idtkn' in resp.cookies)
            # check no other cookies were set
            self.assertEqual(6, len(resp.cookies))
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://account.bbc.com'))


    def test_sign_in(self):
        """Perform a sign in just like  addon"""
        with requests.Session() as s:
            s.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'}
            # Obtain token cookies for domain .bbc.co.uk.
            resp = s.get('https://session.bbc.co.uk/session')
            match = re.search('action="([^"]+)"', resp.text)
            # The link obtained by the regex refers to a url used by webbrowsers to post only the username.
            # We skip that, and immediately post both username and password.
            # Strip the path part from the link to obtain the query string
            query_string = unescape(match[1][5:])
            login_url = 'https://account.bbc.com/auth/password' + query_string
            resp = s.post(login_url,
                          headers={'Origin': 'https://account.bbc.com'},
                          data={'username': credentials.uname,
                                'password': credentials.passw},
                          allow_redirects=False)
            # If sign in is successful the response should redirect to session.bcc.co.uk again.
            if resp.status_code != 302:
                return False
            # Make the request to get the token cookies for the domain .bcc.co.uk
            resp = s.get(resp.headers['location'], allow_redirects=False)
            # This response should redirect back to the main page, but we don't need to follow this.
            # However, on some errors we are redirected back to the account login page, so check the location.
            self.assertEqual(302, resp.status_code)
            self.assertTrue(resp.headers['location'].startswith('https://www.bbc.co'))

            # Obtain token cookies for domain .bbc.com
            # With cookies for account.bbc.com now present, there is no need to provide credentials again.
            # Just follow the redirect to account.bbc.com and the subsequent redirect back to session.bbc.com
            resp = s.get('https://session.bbc.com/session', allow_redirects=False)
            resp = s.get(resp.headers['location'], allow_redirects=False)
            resp = s.get(resp.headers['location'], allow_redirects=False)
            # Again, no need to follow the last redirect, but check its existence.
            self.assertEqual(302, resp.status_code)
            self.assertTrue(resp.headers['location'].startswith('https://www.bbc.co'))

            self.assertGreaterEqual(len(s.cookies), 12)
            return s.cookies


class CheckLoginStatus(TestCase):
    def test_check_logged_in(self):
        signin_test = SignIn()
        # check when actually logged in
        cookies = signin_test.test_sign_in()
        resp = requests.get('https://account.bbc.com/account', cookies=cookies, allow_redirects=False)
        self.assertEqual(200, resp.status_code)

        # check with head request
        resp = requests.head('https://account.bbc.com/account', cookies=cookies, allow_redirects=False)
        self.assertEqual(200, resp.status_code)

    def test_not_logged_in(self):
        # Check when not logged in
        with requests.Session() as session:
            resp = session.get('https://account.bbc.com/account', allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_settings-nonce' in resp.cookies)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.com'))

            resp = session.get(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_nonce' in resp.cookies)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://account.bbc.com/auth'))

    def test_not_logged_in_with_head_request(self):
        # Check when not logged in
        with requests.Session() as session:
            resp = session.head('https://account.bbc.com/account', allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_settings-nonce' in resp.cookies)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://session.bbc.com'))

            resp = session.head(new_url, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_nonce' in resp.cookies)
            new_url = resp.headers['location']
            self.assertTrue(new_url.startswith('https://account.bbc.com/auth'))

    def test_refresh_with_expired_login(self):
        """Check login with expired access tokens, but with valid refresh tokens.

        This effectively is a token refresh.
        Auth redirect to both session.bbc.com, which redirects to session.bbc.co.uk.
        thus picking up all token cookies.

        """
        c_jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        c_jar.load()
        c_jar.save = MagicMock()
        with requests.Session() as session:
            session.cookies = c_jar
            resp = session.get('https://account.bbc.com/account', allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_settings-nonce' in resp.cookies)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://session.bbc.com/session'))

            resp = session.get(new_location, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_atkn' in resp.cookies)
            self.assertTrue('ckns_idtkn' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_nonce' in resp.cookies)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://session.bbc.co.uk/session'))

            resp = session.get(new_location, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_atkn' in resp.cookies)
            self.assertTrue('ckns_idtkn' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_nonce' in resp.cookies)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://account.bbc.com'))

    def test_refresh_with_head_request(self):
        """Check login with expired access tokens, but with valid refresh tokens.

        This effectively is a token refresh.
        Auth redirect to both session.bbc.com, which redirects to session.bbc.co.uk.
        thus pickup all access token cookies.

        """
        c_jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        c_jar.load()
        with requests.Session() as session:
            session.cookies = c_jar
            resp = session.head('https://account.bbc.com/account', allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_settings_nonce' in resp.cookies)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://session.bbc.com'))

            resp = session.head(new_location, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_atkn' in resp.cookies)
            self.assertTrue('ckns_idtkn' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_nonce' in resp.cookies)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://session.bbc.co.uk'))

            resp = session.head(new_location, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            self.assertTrue('ckns_atkn' in resp.cookies)
            self.assertTrue('ckns_idtkn' in resp.cookies)
            self.assertTrue('ckns_id' in resp.cookies)
            self.assertTrue('ckns_nonce' in resp.cookies)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://account.bbc.com'))

    def test_refresh_with_only_a_valid_ckns_jwt_cookie(self):
        """Authenticate against account.bbc.com with just a jwt cookie and all other
        token cookies missing.

        Account accepts and redirects to session, but session refers to login page.
        """
        jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        jar.load()
        jar.clear('.bbc.co.uk')
        jar.clear('.bbc.com')
        jar.clear('.session.bbc.co.uk')
        jar.clear('.session.bbc.com')
        self.assertTrue(any(cookie.name == 'ckns_jwt' for cookie in jar))
        with requests.Session() as session:
            session.cookies = jar
            resp = session.get('https://account.bbc.com/account', allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://session.bbc.com/session'))
            resp = session.get(new_location, allow_redirects=False)
            self.assertEqual(302, resp.status_code)
            new_location = resp.headers['location']
            self.assertTrue(new_location.startswith('https://account.bbc.com/auth'))


    def test_expired_login_at_session(self):
        """Check a request to session with expired access tokens, but with valid refresh tokens.

        Just redirects to the main page, without any authentication.
        """
        resp = requests.get('https://session.bbc.co.uk/session', allow_redirects=False)
        self.assertEqual(302, resp.status_code)
        self.assertFalse('ckns_atkn' in resp.cookies)
        self.assertFalse('ckns_idtkn' in resp.cookies)
        self.assertFalse('ckns_id' in resp.cookies)
        self.assertTrue('ckns_nonce' in resp.cookies)
        new_location = resp.headers['location']
        self.assertTrue(new_location.startswith('https://www.bbc.co.uk'))

    def test_iplayer_statusbbcid(self):
        """Test the function in the addon to get singed-in status"""
        # Check without tokens
        jar = cookiejar.CookieJar()
        jar.save = MagicMock()
        self.assertFalse(ipwww_common.StatusBBCiD(jar))
        jar.save.assert_not_called()
        # Check with expired tokens
        jar = cookiejar.LWPCookieJar(doc_path('cookies/expired.cookies'))
        jar.load()
        jar.save = MagicMock()
        self.assertTrue(ipwww_common.StatusBBCiD(jar))
        jar.save.assert_called_once()
        # Check with already valid tokens
        jar.save.reset_mock()
        self.assertTrue(ipwww_common.StatusBBCiD(jar))
        jar.save.assert_not_called()


class SingOut(TestCase):
    def test_sign_out(self):
        requests.get('https://account.bbc.com/signout?ptrt=https%3A%2F%2Faccount.bbc.com%2Faccount%2Factivity%2F')
        # returns 200 - OK, content-type: text/html
        # a full html page
        requests.get('https://session.bbc.com/session/signout?ptrt=https%3A%2F%2Fsession.bbc.com%2Fsession%2Fannounce&switchTld=1')
        # returns 320 - Found, redirects to the same page, with slightly different query string.
        # sets empty cookies:   ckns_atkn=;     Domain=.bbc.com
        #                       atuserid=;      Domain=.bbc.com
        #                       ckns_sylphid=;  Domain=.bbc.com
        #                       ckns_id=;       Domain=.bbc.com
        #                       ckns_idtkn=;    Domain=.bbc.com
        #                       ckns_rtkn=;     Domain=.session.bbc.com
        # with expire time 1-1-1970.

        requests.get('https://session.bbc.co.uk/session/signout?ptrt=https%3A%2F%2Fsession.bbc.com%2Fsession%2Fannounce')
        # Returns 302 - FOUND, redirects to account.bbc.com
        # No cookies

        requests.get('https://account.bbc.com/account/signout?ptrt=https%3A%2F%2Fsession.bbc.com%2Fsession%2Fannounce&realm=%2F&clientId=Account')
        # Returns 302 - Found, redirects to session.bbc.com
        # sets empty cookies:   ckns_jwt=;      Domain=.account.bbc.com
        #                       ckns_jwt=;      Domain=.bbc.com
        #                       ckns_session=;  Domain=.account.bbc.com
        #                       ckns_session=;  Domain=.bbc.com
        #                       ckns_mvt=;      Domain=.account.bbc.com

        requests.get('https://session.bbc.com/session/announce')
        # Returns 200 - OK, content-type tex/html
        # No cookies
        # Short HTML page:
        # <!DOCTYPE html>
        # <html>
        # <head>
        #   <title>Success</title>
        # </head>
        # <body>
        #   <script type="text/javascript">
        #     if (window.parent) {
        #         parent.postMessage('bbcidv5_token_success', '*');
        #     }
        #   </script>
        # </body>
        # </html>

