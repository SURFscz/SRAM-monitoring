Feature: PAM weblogin
  Scenario Outline: Verifying PAM weblogin for user <user>
     Given SBS health UP
       and we call pam start
       and we use link to login
       and we choose SRAM Monitoring IdP
      When we login as <user>
	  Then we use code to check pam check-pin

  Examples: Test
        | user     |
        | student  |
