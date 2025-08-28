use std::env;
use ratcrawler::*;
use tokio;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🕷️  Rat Crawler - Advanced Web Crawling Tool");
    println!("==========================================");

    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        print_usage();
        return Ok(());
    }

    let command = &args[1];

    match command.as_str() {
        "crawl" => {
            let mut urls = Vec::new();
            let mut max_pages = 100;
            let mut respect_robots_txt = false;
            let mut i = 2;

            while i < args.len() {
                match args[i].as_str() {
                    "--url" => {
                        if i + 1 < args.len() {
                            urls.push(args[i + 1].clone());
                            i += 2;
                        } else {
                            println!("Error: --url requires a value");
                            return Ok(());
                        }
                    }
                    "--max-pages" => {
                        if i + 1 < args.len() {
                            match args[i + 1].parse::<usize>() {
                                Ok(pages) => max_pages = pages,
                                Err(_) => {
                                    println!("Error: --max-pages requires a valid number");
                                    return Ok(());
                                }
                            }
                            i += 2;
                        } else {
                            println!("Error: --max-pages requires a value");
                            return Ok(());
                        }
                    }
                    "--respect-robots-txt" => {
                        if i + 1 < args.len() {
                            match args[i + 1].as_str() {
                                "true" => respect_robots_txt = true,
                                "false" => respect_robots_txt = false,
                                _ => {
                                    println!("Error: --respect-robots-txt requires 'true' or 'false'");
                                    return Ok(());
                                }
                            }
                            i += 2;
                        } else {
                            println!("Error: --respect-robots-txt requires a value");
                            return Ok(());
                        }
                    }
                    _ => {
                        // If it doesn't start with --, treat it as a URL
                        if !args[i].starts_with("--") {
                            urls.push(args[i].clone());
                        } else {
                            println!("Error: Unknown flag '{}'", args[i]);
                            print_usage();
                            return Ok(());
                        }
                        i += 1;
                    }
                }
            }

            if urls.is_empty() {
                println!("Error: Please provide at least one URL to crawl");
                print_usage();
                return Ok(());
            }

            run_web_crawl(urls, max_pages, respect_robots_txt).await?;
        }
        "backlinks" => {
            if args.len() < 3 {
                println!("Error: Please provide URLs to analyze backlinks for");
                print_usage();
                return Ok(());
            }

            let urls: Vec<String> = args[2..].to_vec();
            run_backlink_analysis(urls).await?;
        }
        "integrated" => {
            if args.len() < 3 {
                println!("Error: Please provide URLs for integrated crawling");
                print_usage();
                return Ok(());
            }

            let urls: Vec<String> = args[2..].to_vec();
            run_integrated_crawl(urls).await?;
        }
        "domain" => {
            if args.len() < 3 {
                println!("Error: Please provide a domain to analyze");
                print_usage();
                return Ok(());
            }

            let domain = &args[2];
            run_domain_analysis(domain).await?;
        }
        _ => {
            println!("Error: Unknown command '{}'", command);
            print_usage();
        }
    }

    Ok(())
}

fn print_usage() {
    println!("Usage:");
    println!("  rat-crawler crawl <url1> [url2] ...    - Crawl websites");
    println!("  rat-crawler backlinks <url1> [url2] ... - Analyze backlinks");
    println!("  rat-crawler integrated <url1> [url2] ... - Integrated crawl with backlinks");
    println!("  rat-crawler domain <domain>            - Analyze domain");
    println!();
    println!("Examples:");
    println!("  rat-crawler crawl https://example.com");
    println!("  rat-crawler backlinks https://example.com/page");
    println!("  rat-crawler integrated https://example.com");
    println!("  rat-crawler domain example.com");
}

async fn run_web_crawl(urls: Vec<String>, max_pages: usize, respect_robots_txt: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting web crawl for {} URLs...", urls.len());

    let config = CrawlConfig {
        user_agent: "RatCrawler/1.0".to_string(),
        timeout_secs: 30,
        max_redirects: 5,
        max_depth: 3,
        max_pages,
        delay_ms: 100,
        respect_robots_txt,
    };

    let mut crawler = WebsiteCrawler::new(&config);
    let mut database = WebsiteCrawlerDatabase::new("web_crawl.db")?;

    let result = crawler.crawl(urls, &mut database).await?;

    println!("✅ Crawl completed!");
    println!("📊 Results:");
    println!("   Pages crawled: {}", result.pages_crawled);
    println!("   Errors: {}", result.errors);
    println!("   Session ID: {}", result.session_id);

    Ok(())
}

async fn run_backlink_analysis(urls: Vec<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting backlink analysis for {} URLs...", urls.len());

    let backlink_config = BacklinkConfig {
        user_agent: "RatCrawler-Backlinks/1.0".to_string(),
        timeout_secs: 60,
        max_redirects: 5,
    };

    let processor = BacklinkProcessor::new(
        backlink_config.user_agent,
        backlink_config.timeout_secs,
        backlink_config.max_redirects,
    );

    let database = BacklinkDatabase::new("backlinks.db")?;
    let mut analyzer = BacklinkAnalyzer::new(processor, database);

    for url in urls {
        println!("🔍 Analyzing: {}", url);

        match analyzer.analyze_backlinks(&url).await {
            Ok(analysis) => {
                println!("✅ Analysis completed!");
                println!("   Total backlinks: {}", analysis.total_backlinks);
                println!("   Unique domains: {}", analysis.unique_domains);
                println!("   Spam backlinks: {}", analysis.spam_backlinks);
                println!("   Domain authority: {:.2}", analysis.domain_authority);
                println!("   PageRank score: {:.2}", analysis.pagerank_score);
            }
            Err(e) => {
                println!("❌ Error analyzing {}: {:?}", url, e);
            }
        }
        println!();
    }

    Ok(())
}

async fn run_integrated_crawl(urls: Vec<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting integrated crawl for {} URLs...", urls.len());

    let config = IntegratedCrawlConfig {
        web_crawl_config: CrawlConfig {
            user_agent: "RatCrawler-Integrated/1.0".to_string(),
            timeout_secs: 30,
            max_redirects: 5,
            max_depth: 2,
            max_pages: 50,
            delay_ms: 200,
            respect_robots_txt: true,
        },
        backlink_config: BacklinkConfig {
            user_agent: "RatCrawler-Backlinks/1.0".to_string(),
            timeout_secs: 45,
            max_redirects: 5,
        },
        max_backlink_analyses: 10,
        backlink_timeout_secs: 60,
    };

    let mut crawler = IntegratedCrawler::new(
        "integrated_web.db",
        "integrated_backlinks.db",
        config,
    )?;

    let result = crawler.crawl_website_with_backlinks(urls).await?;

    println!("✅ Integrated crawl completed!");
    println!("📊 Web Crawl Results:");
    println!("   Pages crawled: {}", result.web_crawl_result.pages_crawled);
    println!("   Errors: {}", result.web_crawl_result.errors);
    println!();
    println!("📊 Backlink Analysis Results:");
    println!("   URLs analyzed: {}", result.backlink_analyses.len());

    for (url, analysis) in &result.backlink_analyses {
        println!("   {}: {} backlinks, {} domains",
                 url, analysis.total_backlinks, analysis.unique_domains);
    }

    println!();
    println!("📊 Overall Report:");
    println!("   Total pages: {}", result.report.total_pages_crawled);
    println!("   Total backlinks: {}", result.report.total_backlinks_found);
    println!("   Unique domains: {}", result.report.total_unique_domains);
    println!("   Spam backlinks: {}", result.report.total_spam_backlinks);
    println!("   Avg domain authority: {:.2}", result.report.average_domain_authority);

    Ok(())
}

async fn run_domain_analysis(domain: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting domain analysis for: {}", domain);

    let config = IntegratedCrawlConfig {
        web_crawl_config: CrawlConfig {
            user_agent: "RatCrawler-Domain/1.0".to_string(),
            timeout_secs: 30,
            max_redirects: 5,
            max_depth: 3,
            max_pages: 100,
            delay_ms: 100,
            respect_robots_txt: true,
        },
        backlink_config: BacklinkConfig {
            user_agent: "RatCrawler-Backlinks/1.0".to_string(),
            timeout_secs: 60,
            max_redirects: 5,
        },
        max_backlink_analyses: 5,
        backlink_timeout_secs: 60,
    };

    let mut crawler = IntegratedCrawler::new(
        &format!("domain_{}.db", domain.replace(".", "_")),
        &format!("domain_backlinks_{}.db", domain.replace(".", "_")),
        config,
    )?;

    let result = crawler.crawl_and_analyze_domain(domain).await?;

    println!("✅ Domain analysis completed!");
    println!("📊 Results for domain: {}", result.domain);
    println!("   Pages crawled: {}", result.pages_crawled);
    println!("   Domain authority: {:.2}", result.domain_authority);
    println!("   Crawl errors: {}", result.crawl_errors);
    println!();
    println!("📊 Backlink Analysis:");
    println!("   Total backlinks: {}", result.backlink_analysis.total_backlinks);
    println!("   Unique domains: {}", result.backlink_analysis.unique_domains);
    println!("   Spam backlinks: {}", result.backlink_analysis.spam_backlinks);
    println!("   PageRank score: {:.2}", result.backlink_analysis.pagerank_score);

    Ok(())
}
