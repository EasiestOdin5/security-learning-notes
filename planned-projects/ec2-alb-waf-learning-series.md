# Planned lab series: EC2 web server → Application Load Balancer → AWS WAF

Recorded: October 22, 2026
Status: Planned; no resources provisioned for this series.

## Goal

Build on the VPC Flow Logs lab to understand how network activity becomes an HTTP request, how a load balancer routes it, and how a web application firewall evaluates it. Generate normal traffic first, then compare evidence from each layer before introducing controlled security tests.

## Learning approach

- Work interactively, one step at a time, explaining service behavior before configuration.
- Use complete, ready-to-paste commands and queries with explicit profile, region, log selection, and time-range instructions.
- Start with normal requests and evidence interpretation; defer detection engineering.
- Keep sessions short, avoid NAT Gateways initially, and clean up chargeable resources.
- Aim to keep total lab spending under $10 per month; verify current prices and expected session costs before provisioning, rather than assuming continuous operation fits that budget.

## Starting point

The previous EC2 instance was terminated. Inspect the remaining dedicated VPC, subnets, routing, security groups, IAM delivery role, and CloudWatch log group before reusing resources. Launch a replacement instance and account for its new interface and addresses; the previous ENI-scoped Flow Log will not automatically cover it.

Use us-east-1. The recent lab used CLI profile lab-privileged; confirm the intended administrative profile and caller identity before changes (the original preference was default).

## Stage 1: EC2 web server and client

Use the learner's computer as the client and a small EC2 instance as the web server; a separate client instance is unnecessary initially.

- Establish a minimal web service with access logging.
- Generate known normal requests, including a successful request and a request for a missing resource.
- Inspect request paths, HTTP status codes, timestamps, and client addresses in web server logs.
- Compare these with VPC Flow Logs: network ACCEPT does not establish HTTP success or distinguish 200 from 404.
- Understand what HTTPS encrypts and what the server can still log; introduce TLS configuration as its own step when needed.

## Stage 2: Application Load Balancer

Place an ALB in front of the EC2 web server and send the same requests through it.

- Explain listeners, listener rules, target groups, health checks, and the client-to-ALB and ALB-to-target connections.
- Check subnet and Availability Zone requirements before deployment.
- Configure security groups so the backend receives application traffic from the ALB; examine and close direct-backend bypass as part of the design.
- Enable ALB access logging and compare ALB, web server, and VPC flow evidence for controlled requests.
- Understand client address forwarding and distinguish load balancer responses from target responses.
- Introduce a controlled unhealthy-target or routing failure only after normal behavior is understood.

## Stage 3: AWS WAF

Associate a WAF web ACL with the ALB.

- Explain how request inspection and rule evaluation fit into the request path.
- Begin with a simple, predictable custom rule and observe its count behavior before testing a block.
- Generate a matching test request and a normal request.
- Compare WAF actions and rule matches with ALB logs and backend access logs.
- Verify whether a blocked request reached the backend, rather than assuming a block from an HTTP status alone.
- Explore broader attack-oriented tests only after this baseline is clear.

## Questions this series should answer

- What does each log source prove, and what requires correlation?
- How can network ACCEPT coexist with an HTTP error or a WAF block?
- Which component generated the response?
- How are the original client and the backend connection represented?
- What happens when the ALB considers the target unhealthy?
- How can direct access to the backend bypass the intended WAF-protected path?

## Cost and cleanup

Review current EC2, public IPv4, ALB, WAF, and logging charges before each provisioning phase. Use short-lived sessions and remove resources that continue accruing charges after instance termination, especially the ALB and WAF configuration. Retain only the logs and notes needed for review, with explicit retention settings.

## Completion checkpoint

Explain and trace a normal request, a missing-resource response, and a controlled WAF-blocked request across the relevant logs. Record visibility limitations and cleanup results before deciding whether further automation or detection work is useful.
