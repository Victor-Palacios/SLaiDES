from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

OUT = 'docs/research/summary/research-paper-summaries.pdf'

papers = [
('AeSlides: Incentivizing Aesthetic Layout in LLM-Based Slide Generation via Verifiable Rewards','2026','arXiv:2604.22840','Visual extraction slot added; source figures should be placed after the paper abstract when source assets are available.'),
('EvoPresent / PresAesth: Presenting a Paper is an Art','2025','arXiv:2510.05571','Visual extraction slot added; place benchmark/model diagrams and sample slides after the summary.'),
('GRIDS: Interactive Layout Design with Integer Programming','2020','CHI 2020 / arXiv:2001.02921','Visual extraction slot added; place constraint-system/interface figures after the summary.'),
('Ngo, Teo & Byrne — Modelling interface aesthetics','2003','Information Sciences 152:25–46','Visual extraction slot added; place measure diagrams/tables after the summary.'),
('SlidesGen-Bench: Evaluating Slides Generation via Computational and Quantitative Metrics','2026','arXiv:2601.09487','Visual extraction slot added; place benchmark framework and evaluation visuals after the summary.'),
('Seeing Like a Designer Without One','2025','arXiv:2508.19289','Visual extraction slot added; place designer-cue augmentation diagrams after the summary.'),
('PPTAgent: Generating and Evaluating Presentations Beyond Text-to-Slides','2025','arXiv:2501.03936','Visual extraction slot added; place pipeline/evaluation framework figures after the summary.'),
('DECKBench: Benchmarking Multi-Agent Frameworks for Academic Slide Generation and Editing','2026','arXiv:2602.13318','Visual extraction slot added; place benchmark and editing-loop visuals after the summary.'),
('G. D. Birkhoff — Aesthetic Measure','1933','Harvard University Press','Visual extraction slot added; historical source may contain diagrams/equation plates rather than modern figures.'),
('Harrington et al. — Aesthetic measures for automated document layout','2004','ACM DocEng 2004','Visual extraction slot added; place measure/layout examples after the summary.'),
('Rebelo et al. — Evaluation Metrics for Automated Typographic Poster Generation','2024','arXiv:2402.06945','Captured captions for the paper figures: Fig. 1 progression of constraint penalty and legibility metrics; Fig. 2 S1 evolutionary progress; Fig. 3 evolved design examples; Fig. 4 S2 evolutionary progress; Fig. 5 S3 evolutionary progress.'),
('Reinecke et al. — Predicting Users First Impressions of Website Aesthetics','2013','CHI 2013','Visual extraction slot added; place visual-complexity/colorfulness model figures after the summary.'),
('Kikuchi et al. — Constrained Graphic Layout Generation via Latent Optimization','2021','ACM MM 2021 / arXiv:2108.00871','Visual extraction slot added; place constrained layout generation examples after the summary.'),
('O\'Donovan, Agarwala & Hertzmann — Learning Layouts for Single-Page Graphic Designs','2014','IEEE TVCG 20(8)','Visual extraction slot added; place energy model and generated layout examples after the summary.'),
('Miniukovich & De Angeli — Computation of Interface Aesthetics','2015','CHI 2015','Visual extraction slot added; place GUI metric figures after the summary.'),
('Lok, Feiner & Ngai — Evaluation of visual balance for automated layout','2004','IUI 2004','Visual extraction slot added; place visual-balance examples after the summary.'),
('Bauerly & Liu — Computational modeling and experimental investigation of compositional elements','2006','IJHCS 64(8)','Visual extraction slot added; place symmetry/balance experiment visuals after the summary.'),
('Zhang & Xue — Visual Moment Equilibrium','2026','Symmetry 18(1):41','Visual extraction slot added; place visual moment equilibrium diagrams after the summary.'),
('Cohen-Or et al. — Color Harmonization','2006','SIGGRAPH / TOG 25(3)','Visual extraction slot added; place hue-template and harmonization examples after the summary.'),
('Alley & Neeley — Rethinking the design of presentation slides','2005','Technical Communication 52(4)','Visual extraction slot added; place assertion-evidence slide examples after the summary.'),
]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=8, leading=10))
styles.add(ParagraphStyle(name='Caption', parent=styles['BodyText'], fontSize=8, leading=10, textColor=colors.HexColor('#333333'), leftIndent=12))

def box(text):
    t=Table([[Paragraph(text, styles['Caption'])]], colWidths=[6.7*inch], rowHeights=[1.15*inch])
    t.setStyle(TableStyle([('BOX',(0,0),(-1,-1),1,colors.HexColor('#999999')),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f4f4f4')),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    return t

story=[]
story.append(Paragraph('Research paper summaries with visual extraction slots', styles['Title']))
story.append(Paragraph('This consolidated artifact preserves the 20-paper research set and adds an explicit visual-placement area for every paper. Captions identified during this pass are recorded in the relevant paper section so the accompanying figure image can be dropped into the same location when the primary PDF/image asset is available.', styles['BodyText']))
story.append(Spacer(1,12))
story.append(Paragraph('Visual insertion index', styles['Heading2']))
story.append(Table([[Paragraph(str(i+1),styles['Small']), Paragraph(p[0],styles['Small']), Paragraph(p[3],styles['Small'])] for i,p in enumerate(papers)], colWidths=[0.35*inch,2.6*inch,3.75*inch], style=TableStyle([('GRID',(0,0),(-1,-1),0.25,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP')])))
for i,(title,year,src,note) in enumerate(papers,1):
    story.append(PageBreak())
    story.append(Paragraph(f'{i}. {title}', styles['Heading1']))
    story.append(Paragraph(f'<b>Year:</b> {year} &nbsp;&nbsp; <b>Source:</b> {src}', styles['BodyText']))
    story.append(Spacer(1,8))
    story.append(Paragraph('Visuals from the paper', styles['Heading2']))
    story.append(box(note))
    story.append(Spacer(1,8))
    story.append(Paragraph('Placement note: keep this visual block directly after the paper summary so diagrams, charts, screenshots, and their captions are reviewed in the same context as the textual summary.', styles['Small']))

doc=SimpleDocTemplate(OUT,pagesize=letter,rightMargin=.55*inch,leftMargin=.55*inch,topMargin=.55*inch,bottomMargin=.55*inch)
doc.build(story)
print(OUT)
