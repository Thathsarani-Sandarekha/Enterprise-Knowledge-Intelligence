#!/usr/bin/env python3
"""Generate editable Asteria Studio architecture SVGs and high-resolution PNGs.

This script uses original vector symbols and text rather than third-party logo
files. SVGs can be edited in Inkscape, Illustrator, Figma, or another SVG editor.
"""
from pathlib import Path
import math
import svgwrite
import cairosvg

ROOT = Path(__file__).resolve().parent
FONT = "Inter, Segoe UI, Arial, sans-serif"
C = {
    'navy':'#071725', 'navy2':'#0B2033','navy3':'#102B45','slate':'#233E55',
    'muted':'#92ABC0','white':'#F3F8FC','line':'#33506B','cyan':'#4AD9D6',
    'blue':'#61A5FA','orange':'#FFAD42','purple':'#C4A2FF',
    'green':'#6BE3AF','pink':'#FF8FAD','red':'#FAAB93'
}

class A:
    def __init__(self, name, w, h, eyebrow, title, subtitle, badge):
        self.name, self.w, self.h = name,w,h
        self.d = svgwrite.Drawing(str(ROOT/(name+'.svg')), size=(w,h), viewBox=f'0 0 {w} {h}', profile='full')
        self.d.add(self.d.rect(insert=(0,0), size=(w,h), fill=C['navy']))
        self.d.add(self.d.rect(insert=(0,0), size=(w,158), fill=C['navy2']))
        # blueprint rule
        for x in range(0,w,80):
            self.d.add(self.d.line(start=(x,0),end=(x,158),stroke='#17324A',stroke_width=0.6,opacity=.6))
        self.text(60,38,eyebrow,18,C['orange'],750,spacing=2.2)
        self.text(60,96,title,45,C['white'],780)
        self.text(62,132,subtitle,17,C['muted'],440)
        self.rect(w-360,53,299,48,C['navy3'],'#37516B',16)
        self.text(w-211,84,badge,16,C['white'],700,anchor='middle')
        self.line(60,159,w-60,159,C['line'],1)
    def rect(self,x,y,w,h,fill=None,stroke=None,r=12,sw=1,opacity=1):
        self.d.add(self.d.rect(insert=(x,y),size=(w,h),rx=r,ry=r,fill=fill or 'none',stroke=stroke or 'none',stroke_width=sw,opacity=opacity))
    def line(self,x1,y1,x2,y2,color=C['line'],width=2,dash=None,opacity=1):
        args=dict(start=(x1,y1),end=(x2,y2),stroke=color,stroke_width=width,opacity=opacity,stroke_linecap='round')
        if dash: args['stroke_dasharray']=dash
        self.d.add(self.d.line(**args))
    def poly(self,pts,color=C['cyan'],width=3,dash=None,opacity=1,tip=True):
        args=dict(points=pts,fill='none',stroke=color,stroke_width=width,stroke_linecap='round',stroke_linejoin='round',opacity=opacity)
        if dash: args['stroke_dasharray']=dash
        self.d.add(self.d.polyline(**args))
        if tip:
            x2,y2=pts[-1]; x1,y1=pts[-2]; theta=math.atan2(y2-y1,x2-x1)
            ln=11; spread=5.2
            p1=(x2,y2)
            p2=(x2-ln*math.cos(theta)+spread*math.sin(theta),y2-ln*math.sin(theta)-spread*math.cos(theta))
            p3=(x2-ln*math.cos(theta)-spread*math.sin(theta),y2-ln*math.sin(theta)+spread*math.cos(theta))
            self.d.add(self.d.polygon(points=[p1,p2,p3],fill=color,opacity=opacity))
    def text(self,x,y,s,size=16,fill=None,weight=500,anchor=None,spacing=None):
        attrs=dict(insert=(x,y),font_family=FONT,font_size=size,fill=fill or C['white'],font_weight=str(int(round(weight/100)*100)))
        if anchor: attrs['text_anchor']=anchor
        if spacing: attrs['letter_spacing']=spacing
        self.d.add(self.d.text(s,**attrs))
    def circle(self,x,y,r,fill,stroke=None,sw=1):
        self.d.add(self.d.circle(center=(x,y),r=r,fill=fill,stroke=stroke or 'none',stroke_width=sw))
    def round_label(self,x,y,w,label,accent=C['cyan'],fill='#162F44'):
        self.rect(x,y,w,29,fill,accent,14,1)
        self.text(x+w/2,y+20,label,11,accent,750,anchor='middle',spacing=.9)
    def icon(self,kind,x,y,color=C['cyan'],s=35):
        # x/y are icon center; simple original vector glyphs, no proprietary logo assets
        k=s/34
        if kind in ('database','rds','postgres'):
            self.d.add(self.d.ellipse(center=(x,y-10*k),r=(13*k,5*k),fill='none',stroke=color,stroke_width=2.3))
            self.line(x-13*k,y-10*k,x-13*k,y+10*k,color,2.3)
            self.line(x+13*k,y-10*k,x+13*k,y+10*k,color,2.3)
            self.d.add(self.d.path(d=f'M {x-13*k} {y+10*k} C {x-8*k} {y+17*k}, {x+8*k} {y+17*k}, {x+13*k} {y+10*k}',fill='none',stroke=color,stroke_width=2.3))
            self.d.add(self.d.path(d=f'M {x-13*k} {y} C {x-7*k} {y+6*k}, {x+7*k} {y+6*k}, {x+13*k} {y}',fill='none',stroke=color,stroke_width=2))
        elif kind in ('cloud','s3','storage'):
            self.d.add(self.d.path(d=f'M {x-14*k} {y+7*k} C {x-26*k} {y+7*k}, {x-22*k} {y-5*k}, {x-12*k} {y-5*k} C {x-8*k} {y-20*k}, {x+8*k} {y-18*k}, {x+12*k} {y-7*k} C {x+28*k} {y-7*k}, {x+25*k} {y+8*k}, {x+13*k} {y+8*k} Z',fill='none',stroke=color,stroke_width=2.3,stroke_linejoin='round'))
            self.line(x-6*k,y+2*k,x+7*k,y+2*k,color,2)
        elif kind in ('web','screen','browser'):
            self.rect(x-17*k,y-13*k,34*k,27*k,'none',color,3*k,2)
            self.line(x-16*k,y-4*k,x+16*k,y-4*k,color,1.8)
            for dx in (-11,-6,-1): self.circle(x+dx*k,y-9*k,1.2*k,color)
        elif kind in ('api','gateway','network'):
            for dx,dy in [(-11,-9),(11,-9),(0,12)]: self.circle(x+dx*k,y+dy*k,4*k,'none',color,2)
            for x1,y1,x2,y2 in [(-8,-6,-1,7),(8,-6,1,7),(-7,-9,7,-9)]: self.line(x+x1*k,y+y1*k,x+x2*k,y+y2*k,color,2)
        elif kind in ('shield','iam','auth'):
            self.d.add(self.d.path(d=f'M{x} {y-17*k} L{x+14*k} {y-10*k} L{x+12*k} {y+8*k} Q{x} {y+20*k} {x-12*k} {y+8*k} L{x-14*k} {y-10*k} Z',fill='none',stroke=color,stroke_width=2.4,stroke_linejoin='round'))
            self.d.add(self.d.path(d=f'M{x-5*k} {y} L{x-1*k} {y+5*k} L{x+7*k} {y-5*k}',fill='none',stroke=color,stroke_width=2.2))
        elif kind in ('file','document'):
            self.d.add(self.d.path(d=f'M{x-12*k} {y-16*k} L{x+5*k} {y-16*k} L{x+13*k} {y-8*k} L{x+13*k} {y+17*k} L{x-12*k} {y+17*k} Z M{x+5*k} {y-16*k} L{x+5*k} {y-8*k} L{x+13*k} {y-8*k}',fill='none',stroke=color,stroke_width=2.2,stroke_linejoin='round'))
            self.line(x-5*k,y+1*k,x+6*k,y+1*k,color,2)
            self.line(x-5*k,y+8*k,x+6*k,y+8*k,color,2)
        elif kind in ('worker','cpu','ecs'):
            self.rect(x-13*k,y-13*k,26*k,26*k,'none',color,4*k,2.2)
            self.rect(x-7*k,y-7*k,14*k,14*k,'none',color,2*k,2)
            for a in (-8,0,8):
                self.line(x+a*k,y-18*k,x+a*k,y-13*k,color,1.8)
                self.line(x+a*k,y+13*k,x+a*k,y+18*k,color,1.8)
        elif kind in ('layers','vector','rank'):
            for dy in (-9,0,9):
                self.d.add(self.d.path(d=f'M{x-14*k} {y+dy*k} L{x} {y+(dy-5)*k} L{x+14*k} {y+dy*k} L{x} {y+(dy+5)*k} Z',fill='none',stroke=color,stroke_width=1.9,stroke_linejoin='round'))
        elif kind in ('search','magnifier'):
            self.circle(x-4*k,y-5*k,10*k,'none',color,2.3)
            self.line(x+4*k,y+4*k,x+17*k,y+17*k,color,2.5)
        elif kind in ('ai','llm','spark'):
            self.d.add(self.d.path(d=f'M{x} {y-17*k} L{x+5*k} {y-5*k} L{x+17*k} {y} L{x+5*k} {y+5*k} L{x} {y+17*k} L{x-5*k} {y+5*k} L{x-17*k} {y} L{x-5*k} {y-5*k} Z',fill='none',stroke=color,stroke_width=2.2,stroke_linejoin='round'))
            self.circle(x+15*k,y-12*k,2.4*k,color)
        elif kind in ('code','ecr','git'):
            self.d.add(self.d.path(d=f'M{x-7*k} {y-11*k} L{x-17*k} {y} L{x-7*k} {y+11*k} M{x+7*k} {y-11*k} L{x+17*k} {y} L{x+7*k} {y+11*k} M{x+4*k} {y-16*k} L{x-4*k} {y+16*k}',fill='none',stroke=color,stroke_width=2.5,stroke_linecap='round',stroke_linejoin='round'))
        elif kind in ('clock','watch','monitor'):
            self.circle(x,y,14*k,'none',color,2.2)
            self.line(x,y,x,y-8*k,color,2.2)
            self.line(x,y,x+7*k,y+4*k,color,2.2)
        elif kind in ('key','secrets'):
            self.circle(x-8*k,y-5*k,8*k,'none',color,2.2)
            self.line(x-2*k,y+2*k,x+15*k,y+16*k,color,2.2)
            self.line(x+8*k,y+9*k,x+14*k,y+3*k,color,2.2)
        else:
            self.circle(x,y,12*k,'none',color,2.4)
    def card(self,x,y,w,h,title,detail,kind,accent=C['cyan'],badge=None,compact=False):
        self.rect(x,y,w,h,C['navy3'],'#365572',15,1.1)
        self.rect(x+16,y+18,50,50,'#183B57',None,11)
        self.icon(kind,x+41,y+43,accent,28)
        self.text(x+82,y+(41 if compact else 43),title,19 if not compact else 17,C['white'],760)
        for i,line in enumerate(detail):
            self.text(x+82,y+(69 if compact else 74)+i*21,line,13 if compact else 14,C['muted'],430)
        if badge:
            ww=max(85,len(badge)*7+20)
            self.round_label(x+w-ww-16,y+h-39,ww,badge,accent)
    def panel(self,x,y,w,h,num,title,subtitle,accent):
        self.rect(x,y,w,h,'#0D243A','#26455E',20,1.2)
        self.rect(x+20,y+21,45,34,accent,None,10)
        self.text(x+42.5,y+44,str(num).zfill(2),14,C['navy'],800,anchor='middle')
        self.text(x+81,y+44,title,20,C['white'],740)
        self.text(x+w-26,y+44,subtitle,13,C['muted'],500,anchor='end')
        self.line(x+23,y+68,x+w-23,y+68,C['line'],1)
    def save(self):
        self.d.save(pretty=True)
        cairosvg.svg2png(url=str(ROOT/(self.name+'.svg')),write_to=str(ROOT/(self.name+'.png')),output_width=int(self.w*1.35),output_height=int(self.h*1.35))

# DIAGRAM A: IMPLMENTATION
A1=A('implemented-system',2000,1260,'ASTERIA / TECHNICAL ARCHITECTURE','Implemented platform','Real application services, AWS SDK integration and evidence-grounded retrieval','IMPLEMENTED / CODE')
A1.panel(48,194,1904,203,1,'Experience & API','application service boundary',C['cyan'])
for x,t,d,k,a in [
 (80,'Next.js workspace',['Studio roles • document library','Search, Q&A, grouped citations'],'web',C['blue']),
 (558,'Server-side gateway',['REST proxy / API key handling','Frontend → FastAPI'],'gateway',C['cyan']),
 (1036,'FastAPI services',['Upload • documents • search','Knowledge questions'],'api',C['green']),
 (1514,'Tenant & role grants',['SQL-scoped document access','Simulated demo identities'],'shield',C['purple'])]:
 A1.card(x,285,400,97,t,d,k,a,compact=True)
for x in [480,958,1436]: A1.poly([(x,333),(x+78,333)],C['cyan'],2.8)
A1.panel(48,419,1904,335,2,'Document intelligence pipeline','PDF · DOCX · XLSX → indexed knowledge',C['orange'])
xs=[75,455,835,1215,1595]; ws=[330]*5
cards=[('Upload & validate',['File checks • SHA-256','Queue metadata and grants'],'document',C['blue']),
('AWS S3 integration',['Boto3 object adapter','Filesystem fallback'],'s3',C['orange']),
('Python worker',['Persistent DB job queue','Queued → ready / failed'],'worker',C['purple']),
('Docling + OpenPyXL',['OCR / parsing • chunks','Source locations retained'],'file',C['green']),
('Sentence embeddings',['Local model • 384-D','SQL + vector indexing'],'vector',C['cyan'])]
for x,(t,d,k,c) in zip(xs,cards): A1.card(x,527,330,128,t,d,k,c)
for i,x in enumerate(xs[:-1]): A1.poly([(x+330,588),(xs[i+1],588)],C['orange'] if i==0 else C['blue'],2.8)
A1.rect(260,685,1480,50,'#172F46','#365572',14)
A1.icon('database',297,710,C['green'],21)
A1.text(330,716,'POSTGRESQL + PGVECTOR',18,C['white'],760)
A1.text(725,715,'document metadata  •  roles & tenant grants  •  text search  •  384-D embeddings',15,C['muted'])
A1.poly([(1760,654),(1760,711),(1740,711)],C['green'],2.5)
A1.panel(48,779,1904,369,3,'Permission-aware RAG & answer generation','only authorized excerpts reach Groq',C['blue'])
xs=[72,453,834,1215,1596]
cards=[('Scoped retrieval',['Tenant + role predicates','Apply before candidate ranking'],'shield',C['purple']),
('Hybrid search',['Postgres full-text + pgvector','Lexical and semantic branches'],'search',C['blue']),
('RRF + reranking',['Reciprocal rank fusion','Cross-encoder passage scoring'],'layers',C['cyan']),
('Groq inference',['Structured JSON responses','openai/gpt-oss-20b'],'spark',C['orange']),
('Citation verification',['Evidence IDs + source excerpts','Document-grouped UI output'],'file',C['green'])]
for x,(t,d,k,c) in zip(xs,cards): A1.card(x,887,330,149,t,d,k,c)
for i,x in enumerate(xs[:-1]): A1.poly([(x+330,951),(xs[i+1],951)],C['blue'],2.8)
A1.poly([(650,735),(650,860),(590,860),(590,887)],C['green'],2.5)
A1.round_label(255,1077,315,'BACKEND ENFORCED ACCESS',C['purple'])
A1.round_label(637,1077,360,'EXACT SOURCE-EXCERPT CHECKS',C['green'])
A1.round_label(1067,1077,270,'GROQ STRUCTURED JSON',C['orange'])
A1.round_label(1397,1077,330,'DOCKER / COMPOSE PACKAGING',C['blue'])
A1.text(60,1205,'IMPLEMENTED: FastAPI • Next.js • SQL ACL • Docling • Boto3 S3 adapter • worker • RRF / reranker • Groq • citations',13,C['muted'])
A1.text(1940,1205,'ASTERIA STUDIO  /  01',13,C['muted'],anchor='end')
A1.save()

# DIAGRAM B: AWS PRODUCTION REFERENCE
B=A('aws-production-reference',2000,1260,'ASTERIA / ENTERPRISE CLOUD BLUEPRINT','AWS production reference architecture','A deployment design mapping the current codebase to managed AWS services','AWS REFERENCE / DESIGN')
# separate external identities
B.rect(48,241,242,136,C['navy3'],'#365572',17)
B.icon('web',90,289,C['blue'],30)
B.text(123,292,'Studio users',20,C['white'],730)
B.text(73,339,'Design • PM • Procurement',14,C['muted'])
B.rect(48,489,242,155,C['navy3'],'#365572',17)
B.icon('ai',90,539,C['orange'],30)
B.text(125,541,'Groq LLM',19,C['white'],740)
B.text(72,578,'External hosted inference',14,C['muted'])
B.text(72,602,'Structured answers + citations',12,C['muted'])
B.rect(48,777,242,155,C['navy3'],'#365572',17)
B.icon('git',90,831,C['purple'],30)
B.text(121,829,'GitHub Actions',17,C['white'],740)
B.text(72,869,'Build, test, publish images',13,C['muted'])
B.text(72,893,'CI/CD design',12,C['purple'])
# AWS boundary
B.rect(317,195,1635,991,'#10243A','#C87B2C',26,2)
B.rect(339,208,173,42,'#8E5419',None,14)
B.text(428,236,'AWS CLOUD',18,'#FFF7E8',800,anchor='middle',spacing=1)
B.text(551,235,'Region / VPC / private application subnets',16,C['muted'],500)
B.round_label(1712,216,215,'PROPOSED DEPLOYMENT',C['orange'])
B.panel(347,265,1573,204,1,'Edge, identity & API ingress','HTTPS • verified identity • private integration',C['orange'])
xs=[373,760,1147,1534]
for x,(t,d,k,a) in zip(xs,[
('CloudFront + ALB',['Web delivery / HTTPS','Routes to Next.js'],'cloud',C['orange']),
('Amazon Cognito',['OIDC / verified principals','User and tenant claims'],'shield',C['pink']),
('API Gateway',['HTTP API entry point','JWT authorization'],'gateway',C['blue']),
('VPC Link + ALB',['Private API integration','Traffic to FastAPI tasks'],'network',C['cyan'])]):
 B.card(x,352,354,100,t,d,k,a,compact=True)
# Cognito is a JWT identity provider, not a hop for application traffic.
B.poly([(1114,405),(1147,405)],C['pink'],2.5,dash='5 5')
B.poly([(1501,405),(1534,405)],C['cyan'],2.8)
B.panel(347,492,1573,253,2,'Containerized application services','ECS Fargate services • images in ECR',C['cyan'])
xs=[373,760,1147,1534]
for x,(t,d,k,a) in zip(xs,[
('Amazon ECR',['Versioned Docker images','GitHub Actions build target'],'ecr',C['orange']),
('ECS • Next.js',['Website and server gateway','Stateless web service'],'ecs',C['blue']),
('ECS • Worker',['Database-backed queue','Docling / embeddings'],'worker',C['purple']),
('ECS • FastAPI',['Knowledge API + permissions','RAG / Groq integration'],'api',C['cyan'])]):
 B.card(x,582,354,120,t,d,k,a)
B.poly([(549,930),(549,831),(549,747),(549,702)],C['orange'],2,dash='7 6',opacity=.65,tip=False) if False else None
# Application request paths: web delivery, API calls, private ingress.
B.poly([(550,452),(550,477),(908,477),(908,582)],C['orange'],2.5)
B.poly([(1114,634),(1133,634),(1133,480),(1324,480),(1324,452)],C['blue'],2.5)
B.poly([(1711,452),(1711,582)],C['cyan'],2.6)
# ECR provides images to the three ECS services (deployment, not user traffic).
B.poly([(727,632),(760,632)],C['orange'],2,dash='5 6')
# Groq hosted inference is a provider API outside AWS.
B.poly([(1711,702),(1711,756),(315,756),(315,567),(290,567)],C['orange'],2.6)
B.panel(347,769,1573,246,3,'Managed data & secure integration','private object storage • relational/vector data',C['green'])
xs=[373,894,1415]
for x,(t,d,k,a) in zip(xs,[
('Amazon S3',['Original PDF / DOCX / XLSX','Boto3 object access'],'s3',C['orange']),
('Amazon RDS PostgreSQL',['Metadata • grants • pgvector','Hybrid SQL + vector indexes'],'rds',C['blue']),
('IAM + Secrets Manager',['Task roles • provider secrets','Least-privilege access'],'iam',C['pink'])]):
 B.card(x,864,480,128,t,d,k,a)
# Durable data paths from FastAPI / ingestion worker to AWS storage.
B.poly([(1324,702),(1324,765),(870,765),(870,845),(613,845),(613,864)],C['green'],2.4)
B.poly([(1711,702),(1711,747),(1125,747),(1125,864)],C['blue'],2.4)
B.panel(347,1037,1573,119,4,'Observability and operations','CloudWatch logs / metrics / alarms · VPC controls · TLS',C['purple'])
B.rect(375,1100,1516,40,'#173651','#38536D',12)
B.icon('watch',408,1121,C['purple'],20)
B.text(441,1127,'CloudWatch collects logs, operational metrics and application alarms from ECS / AWS services',16,C['white'],580)
# external flows clean routes
B.poly([(290,308),(317,308),(317,400),(373,400)],C['orange'],3)
B.poly([(290,849),(326,849),(326,643),(373,643)],C['purple'],2.6,dash='7 7')
B.text(50,1196,'REFERENCE VIEW: AWS compute, ingress, identity and monitoring are proposed. Existing Boto3 integration maps to Amazon S3.',14,C['muted'])
B.text(1945,1196,'ASTERIA STUDIO  /  02',13,C['muted'],anchor='end')
B.save()

# DIAGRAM C: SPECIALIZED DOCUMENT + RAG PATH
F=A('rag-workflow',2000,1040,'ASTERIA / MODEL AND DATA FLOW','Document-to-answer pipeline','Two execution paths • durable ingestion and permission-scoped evidence synthesis','TECHNICAL WORKFLOW')
F.panel(50,200,1900,333,1,'Document ingestion','asynchronous • durable • source-aware',C['orange'])
xs=[80,463,846,1229,1612]
for x,(t,d,k,a) in zip(xs,[
('Upload',[ 'PDF • DOCX • XLSX','Size / hash / ACL checks'],'document',C['blue']),
('AWS S3 / adapter',['Boto3 object key','Filesystem alternative'],'s3',C['orange']),
('Python worker',['DB queue • SKIP LOCKED','Status transitions'],'worker',C['purple']),
('Parse + chunk',['Docling / OpenPyXL','Source coordinates'],'file',C['green']),
('Embed + index',['384-D vectors','SQL text + pgvector'],'vector',C['cyan'])]): F.card(x,305,308,154,t,d,k,a)
for i in range(4): F.poly([(xs[i]+308,382),(xs[i+1],382)],C['orange'],3)
F.rect(600,480,800,33,'#24445C',None,11)
F.text(1000,501,'DATABASE: DOCUMENTS • ROLE GRANTS • CHUNKS • EMBEDDINGS',13,C['white'],740,anchor='middle',spacing=.3)
F.panel(50,559,1900,341,2,'Evidence-grounded knowledge retrieval','online query • authorization before LLM context',C['cyan'])
for x,(t,d,k,a) in zip(xs,[
('Query + identity',['Next.js → FastAPI','Trusted demo context'],'web',C['blue']),
('Authorized search',['SQL tenant / role filter','Keyword + vector'],'shield',C['purple']),
('Rank passages',['RRF merges lists','Cross-encoder reranking'],'layers',C['cyan']),
('Groq structured LLM',['Evidence and question','JSON draft answer'],'ai',C['orange']),
('Verify + render',['Exact source quotations','Grouped citation audit'],'file',C['green'])]): F.card(x,669,308,160,t,d,k,a)
for i in range(4): F.poly([(xs[i]+308,747),(xs[i+1],747)],C['cyan'],3)
F.poly([(1000,513),(1000,540),(1000,555),(625,555),(625,669)],C['green'],2.4)
F.round_label(110,928,430,'BOUNDARY A: TENANT / DOCUMENT GRANTS',C['purple'])
F.round_label(595,928,430,'BOUNDARY B: EVIDENCE BEFORE GENERATION',C['cyan'])
F.round_label(1080,928,390,'BOUNDARY C: QUOTE VERIFICATION',C['green'])
F.text(63,1000,'SOURCE PROVENANCE: filenames, project codes, DOCX sections, PDF locators and XLSX cell ranges retained for inspection',14,C['muted'])
F.text(1935,1000,'ASTERIA STUDIO  /  03',13,C['muted'],anchor='end')
F.save()

# COVER asset
w,h=2000,510
D=svgwrite.Drawing(str(ROOT/'asteria-banner.svg'),size=(w,h),viewBox=f'0 0 {w} {h}')
D.add(D.rect(insert=(0,0),size=(w,h),fill='#071725'))
for x in range(0,w,100): D.add(D.line(start=(x,0),end=(x,h),stroke='#172F46',stroke_width=.8,opacity=.6))
for y in range(0,h,68): D.add(D.line(start=(0,y),end=(w,y),stroke='#172F46',stroke_width=.8,opacity=.6))
D.add(D.rect(insert=(51,52),size=(115,8),rx=4,fill=C['orange']))
def tt(x,y,s,fs,color,fw): D.add(D.text(s,insert=(x,y),font_size=fs,font_family=FONT,fill=color,font_weight=str(int(round(fw/100)*100))))
tt(55,125,'ASTERIA  /  STUDIO',33,C['orange'],790)
tt(52,243,'Enterprise Knowledge',90,C['white'],790)
tt(52,342,'Intelligence Platform',90,C['white'],790)
tt(56,398,'AWS-integrated document intelligence  •  hybrid RAG  •  evidence-grounded answers',30,C['muted'],450)
# decorative layered illustration on right
for x,y,r,color in [(1720,170,180,'#1D4562'),(1810,270,150,'#1E5B68'),(1690,320,120,'#29465C')]:
 D.add(D.circle(center=(x,y),r=r,fill='none',stroke=color,stroke_width=2.5,opacity=.65))
for x,y,label,color in [(1530,160,'AWS S3',C['orange']),(1685,258,'PGVECTOR',C['blue']),(1530,355,'GROQ',C['green'])]:
 D.add(D.rect(insert=(x,y),size=(202,62),rx=15,fill='#14304A',stroke=color,stroke_width=1.7))
 tt(x+25,y+42,label,22,C['white'],700)
D.save()
cairosvg.svg2png(url=str(ROOT/'asteria-banner.svg'),write_to=str(ROOT/'asteria-banner.png'),output_width=2400,output_height=612)
print('Generated:',*[str(p) for p in sorted(ROOT.glob('*')) if p.suffix in {'.svg','.png'}],sep='\n  ')
