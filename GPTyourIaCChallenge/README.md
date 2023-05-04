For the challenge, I figured a good viable target was:

- EC2 web server
- All that's required for EC2 to access the internet
- Set the test page to "Hello world from Pulumi AI"

It did take quite some back and forth with Pulumi AI via the web portal, but it got there in the end.  It initially forgot things like:

- Looking up the AMI ID dynamicallly
- Attaching the route table to the subnet
- Binding a public IP to the web server

I did go a little further and got it to add an instance profile + role to allow SSM connect, instead of bothering with an SSH key.