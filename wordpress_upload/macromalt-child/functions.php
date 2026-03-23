<?php
/**
 * Macromalt Child Theme functions and definitions
 *
 * DESIGN TRACK: Step04 - Seasonal Layer Refinement [Merged]
 * PHASE 20: Technical SEO Baseline + Monetization Architecture
 * 
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // Exit if accessed directly.
}

/**
 * 1. Step02 - Global Shell & IA Refinement
 */

// 1.1 Homepage Editorial Masthead (Hero) Injection
add_action( 'generate_after_header', function() {
    if ( is_front_page() && ! is_paged() ) {
        ?>
        <div class="editorial-masthead">
            <div class="grid-container">
                <h1 class="masthead-title">MACROMALT</h1>
                <p class="masthead-tagline">INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO</p>
            </div>
        </div>
        <?php
    }
}, 15 );

// 1.2 Breadcrumb & Category Badge Injection
add_action( 'generate_before_content', function() {
    if ( is_front_page() || is_search() ) {
        return;
    }

    echo '<div class="editorial-shell-meta">';
    if ( is_category() ) {
        echo '<span class="shell-badge">CATEGORY:</span> ' . single_cat_title( '', false );
    } elseif ( is_single() ) {
        echo '<span class="shell-badge">INSIGHT:</span> ';
        the_category( ', ' );
    }
    echo '</div>';
}, 5 );

/**
 * 2. Step03 - Utility & Trust Surface Refinement
 */

// 2.1 Disclosure & Methodology Box (Single Posts Only)
add_action( 'generate_before_content', function() {
    if ( is_single() && ! is_page() ) {
        $disclosure_text = '';
        if ( has_category( 'analysis' ) ) {
            $disclosure_text = '본 분석은 공개적으로 확인 가능한 경제지표, 기업 공시, 실적 자료, 정책 발표, 그리고 신뢰 가능한 리서치 자료를 바탕으로 작성되었다.';
        } elseif ( has_category( 'picks' ) ) {
            $disclosure_text = '본 콘텐츠는 정보 제공 및 해석 목적의 에디토리얼 리서치이며, 특정 자산에 대한 투자 권유를 의미하지 않는다. 시장 환경은 빠르게 변할 수 있으며, 최종 투자 판단과 그 결과에 대한 책임은 이용자 본인에게 있다.';
        } else {
            // Default or Fallback Text
            $disclosure_text = '본 콘텐츠는 정보 제공을 목적으로 하는 에디토리얼 리서치이며, 최종 투자 판단과 결과에 대한 책임은 이용자 본인에게 있습니다.';
        }

        echo '<div class="editorial-disclosure-box">
                <span class="disclosure-heading">DISCLOSURE & METHODOLOGY</span>
                ' . esc_html( $disclosure_text ) . '
              </div>';
    }
}, 10 );

// 2.2 Search Results Header
add_action( 'generate_before_main_content', function() {
    if ( is_search() ) {
        echo '<div class="search-results-label">SEARCHING THE MACROMALT ARCHIVE:</div>';
    }
}, 5 );

// 2.3 Footer Trust Micro-layer (Append)
add_action( 'generate_after_footer_content', function() {
    echo '<div class="footer-trust-layer">
            © 2026 MACROMALT. ALL RIGHTS RESERVED. INSTITUTIONAL RESEARCH FOR THE GLOBAL MACRO.
          </div>';
}, 20 );

// 2.4 Read More Text Refinement (Robust Filters)
add_filter( 'generate_excerpt_more', function( $more ) {
    return ' ...';
}, 20 );

add_filter( 'generate_content_more_link_output', 'macromalt_customize_read_more', 20 );
add_filter( 'generate_excerpt_more_output', 'macromalt_customize_read_more', 20 );
function macromalt_customize_read_more() {
    return sprintf(
        '<p class="read-more-container"><a title="%1$s" class="read-more" href="%2$s">%3$s</a></p>',
        the_title_attribute( 'echo=0' ),
        esc_url( get_permalink() ),
        __( 'FULL ANALYSIS →', 'generatepress' )
    );
}

/**
 * 3. Step04 - Seasonal Layer
 */

// 3.1 Deterministic Seasonal Class (WP Timezone)
add_filter( 'body_class', function( $classes ) {
    // WordPress 로컬 타임존 기반 월 식별 [jan, feb...]
    $month = strtolower( current_time( 'M' ) ); 
    $classes[] = 'mm-season-' . $month;
    return $classes;
} );

/**
 * 4. Enqueue Parent Styles
 */
add_action( 'wp_enqueue_scripts', function() {
    wp_enqueue_style( 'generatepress-style', get_template_directory_uri() . '/style.css' );
}, 1 );

/**
 * ─────────────────────────────────────────────────────────────
 * 5. Technical SEO Baseline (Phase 20)
 * ─────────────────────────────────────────────────────────────
 */

// 5.1 Robots meta directives — noindex for thin/duplicate pages
add_action( 'wp_head', function() {
    if ( is_search() || is_date() || is_tag() ) {
        echo '<meta name="robots" content="noindex, follow">' . "\n";
    }
}, 1 );

// 5.2 Canonical URL injection
add_action( 'wp_head', function() {
    $canonical = '';
    if ( is_singular() ) {
        $canonical = get_permalink();
    } elseif ( is_category() ) {
        $canonical = get_category_link( get_queried_object_id() );
    } elseif ( is_front_page() ) {
        $canonical = home_url( '/' );
    } elseif ( is_paged() ) {
        $canonical = get_pagenum_link( get_query_var( 'paged' ) );
    }
    if ( $canonical ) {
        echo '<link rel="canonical" href="' . esc_url( $canonical ) . '">' . "\n";
    }
}, 5 );

// 5.3 Meta description injection
add_action( 'wp_head', function() {
    $description = '';
    if ( is_singular() ) {
        $post = get_queried_object();
        if ( has_excerpt( $post->ID ) ) {
            $description = wp_strip_all_tags( get_the_excerpt( $post->ID ) );
        } else {
            $description = wp_trim_words(
                wp_strip_all_tags( get_the_content( null, false, $post->ID ) ),
                25,
                '...'
            );
        }
    } elseif ( is_front_page() ) {
        $description = 'Macromalt — 글로벌 매크로를 위한 기관 수준의 리서치. 한국 주식시장, 거시경제 트렌드, 투자 테마를 데이터 기반으로 분석한다.';
    } elseif ( is_category() ) {
        $cat_desc    = category_description();
        $description = $cat_desc
            ? wp_strip_all_tags( $cat_desc )
            : single_cat_title( '', false ) . ' — Macromalt 기관 리서치 아카이브.';
    }
    if ( $description ) {
        echo '<meta name="description" content="' . esc_attr( mb_substr( wp_strip_all_tags( $description ), 0, 160 ) ) . '">' . "\n";
    }
}, 6 );

// 5.4 Open Graph + Twitter Card metadata
add_action( 'wp_head', function() {
    $og_title       = '';
    $og_description = '';
    $og_url         = '';
    $og_image       = '';
    $og_type        = 'website';

    if ( is_singular() ) {
        $post           = get_queried_object();
        $og_type        = 'article';
        $og_title       = get_the_title( $post->ID );
        $og_url         = get_permalink( $post->ID );
        if ( has_excerpt( $post->ID ) ) {
            $og_description = wp_strip_all_tags( get_the_excerpt( $post->ID ) );
        } else {
            $og_description = wp_trim_words(
                wp_strip_all_tags( get_the_content( null, false, $post->ID ) ),
                25,
                '...'
            );
        }
        if ( has_post_thumbnail( $post->ID ) ) {
            $og_image = get_the_post_thumbnail_url( $post->ID, 'large' );
        }
    } elseif ( is_front_page() ) {
        $og_title       = get_bloginfo( 'name' );
        $og_description = '글로벌 매크로를 위한 기관 수준의 리서치.';
        $og_url         = home_url( '/' );
    } elseif ( is_category() ) {
        $og_title = single_cat_title( '', false ) . ' — Macromalt';
        $og_url   = get_category_link( get_queried_object_id() );
    }

    $og_title       = $og_title ?: get_bloginfo( 'name' );
    $og_url         = $og_url ?: home_url( '/' );
    $og_description = $og_description
        ? mb_substr( wp_strip_all_tags( $og_description ), 0, 200 )
        : '';

    echo '<meta property="og:site_name" content="Macromalt">' . "\n";
    echo '<meta property="og:type" content="' . esc_attr( $og_type ) . '">' . "\n";
    echo '<meta property="og:title" content="' . esc_attr( $og_title ) . '">' . "\n";
    echo '<meta property="og:url" content="' . esc_url( $og_url ) . '">' . "\n";
    if ( $og_description ) {
        echo '<meta property="og:description" content="' . esc_attr( $og_description ) . '">' . "\n";
    }
    if ( $og_image ) {
        echo '<meta property="og:image" content="' . esc_url( $og_image ) . '">' . "\n";
    }

    $tw_card = $og_image ? 'summary_large_image' : 'summary';
    echo '<meta name="twitter:card" content="' . esc_attr( $tw_card ) . '">' . "\n";
    echo '<meta name="twitter:title" content="' . esc_attr( $og_title ) . '">' . "\n";
    if ( $og_description ) {
        echo '<meta name="twitter:description" content="' . esc_attr( $og_description ) . '">' . "\n";
    }
    if ( $og_image ) {
        echo '<meta name="twitter:image" content="' . esc_url( $og_image ) . '">' . "\n";
    }
}, 7 );

// 5.5 Schema.org structured data (JSON-LD)
add_action( 'wp_head', function() {

    // Organization — every page
    $org = [
        '@context'    => 'https://schema.org',
        '@type'       => 'Organization',
        'name'        => 'Macromalt',
        'url'         => home_url( '/' ),
        'description' => '글로벌 매크로를 위한 기관 수준의 리서치.',
    ];
    echo '<script type="application/ld+json">' . wp_json_encode( $org, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";

    // WebSite — front page only
    if ( is_front_page() ) {
        $website = [
            '@context' => 'https://schema.org',
            '@type'    => 'WebSite',
            'name'     => 'Macromalt',
            'url'      => home_url( '/' ),
        ];
        echo '<script type="application/ld+json">' . wp_json_encode( $website, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
    }

    // Article + BreadcrumbList — single posts only
    if ( is_singular( 'post' ) ) {
        $post        = get_queried_object();
        $author_name = get_the_author_meta( 'display_name', $post->post_author );
        $author_url  = get_author_posts_url( $post->post_author );
        $thumb_url   = has_post_thumbnail( $post->ID )
            ? get_the_post_thumbnail_url( $post->ID, 'large' )
            : '';

        $desc = has_excerpt( $post->ID )
            ? wp_strip_all_tags( get_the_excerpt( $post->ID ) )
            : wp_trim_words( wp_strip_all_tags( get_the_content( null, false, $post->ID ) ), 30, '...' );

        $article = [
            '@context'         => 'https://schema.org',
            '@type'            => 'Article',
            'headline'         => get_the_title( $post->ID ),
            'description'      => mb_substr( $desc, 0, 200 ),
            'datePublished'    => get_the_date( 'c', $post->ID ),
            'dateModified'     => get_the_modified_date( 'c', $post->ID ),
            'author'           => [ '@type' => 'Person', 'name' => $author_name, 'url' => $author_url ],
            'publisher'        => [ '@type' => 'Organization', 'name' => 'Macromalt', 'url' => home_url( '/' ) ],
            'mainEntityOfPage' => [ '@type' => 'WebPage', '@id' => get_permalink( $post->ID ) ],
        ];
        if ( $thumb_url ) {
            $article['image'] = $thumb_url;
        }
        echo '<script type="application/ld+json">' . wp_json_encode( $article, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";

        // BreadcrumbList
        $cats   = get_the_category( $post->ID );
        $items  = [ [ '@type' => 'ListItem', 'position' => 1, 'name' => 'Macromalt', 'item' => home_url( '/' ) ] ];
        if ( ! empty( $cats ) ) {
            $items[] = [ '@type' => 'ListItem', 'position' => 2, 'name' => $cats[0]->name, 'item' => get_category_link( $cats[0]->term_id ) ];
            $items[] = [ '@type' => 'ListItem', 'position' => 3, 'name' => get_the_title( $post->ID ), 'item' => get_permalink( $post->ID ) ];
        } else {
            $items[] = [ '@type' => 'ListItem', 'position' => 2, 'name' => get_the_title( $post->ID ), 'item' => get_permalink( $post->ID ) ];
        }
        $breadcrumb = [ '@context' => 'https://schema.org', '@type' => 'BreadcrumbList', 'itemListElement' => $items ];
        echo '<script type="application/ld+json">' . wp_json_encode( $breadcrumb, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . '</script>' . "\n";
    }
}, 8 );

// 5.6 Sitemap: exclude tag taxonomy from native WordPress sitemap
add_filter( 'wp_sitemaps_taxonomies', function( $taxonomies ) {
    unset( $taxonomies['post_tag'] );
    return $taxonomies;
} );

// 5.6b Sitemap: exclude users
add_filter( 'wp_sitemaps_add_provider', function( $provider, $name ) {
    return $name === 'users' ? false : $provider;
}, 10, 2 );

// 5.7 robots.txt: append Macromalt crawl policy and sitemap pointer
add_filter( 'robots_txt', function( $output, $public ) {
    $output .= "\n# Macromalt SEO Policy\n";
    $output .= "Disallow: /?s=\n";
    $output .= "Disallow: /search/\n";
    return $output;
}, 10, 2 );

/**
 * ─────────────────────────────────────────────────────────────
 * 6. Monetization Architecture (Phase 20 — Scaffold / INACTIVE)
 *
 * INACTIVE: flip MACROMALT_ADSENSE_ACTIVE to true only after
 * AdSense site approval and MACROMALT_ADSENSE_PUBLISHER_ID is set.
 * ─────────────────────────────────────────────────────────────
 */
define( 'MACROMALT_ADSENSE_ACTIVE', false );
// define( 'MACROMALT_ADSENSE_PUBLISHER_ID', 'pub-XXXXXXXXXXXXXXXX' ); // set after approval

// 6.1 AdSense script loader (fires only when active + page is eligible)
add_action( 'wp_head', function() {
    if ( ! MACROMALT_ADSENSE_ACTIVE ) {
        return;
    }
    // Excluded: about, privacy, terms, disclosure pages and author archives
    if ( is_page( [ 'about', 'privacy-policy', 'terms', 'advertising-policy', 'disclosure' ] ) || is_author() ) {
        return;
    }
    $pub_id = defined( 'MACROMALT_ADSENSE_PUBLISHER_ID' ) ? MACROMALT_ADSENSE_PUBLISHER_ID : '';
    if ( ! $pub_id ) {
        return;
    }
    echo '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' . esc_attr( $pub_id ) . '" crossorigin="anonymous"></script>' . "\n";
}, 20 );

// 6.2 Single post: mid-article ad slot (injected after paragraph 4)
add_filter( 'the_content', function( $content ) {
    if ( ! is_single() || is_page() || ! MACROMALT_ADSENSE_ACTIVE ) {
        return $content;
    }
    $paragraphs = explode( '</p>', $content );
    if ( count( $paragraphs ) > 6 ) {
        $slot = '<div class="mm-ad-slot mm-ad-mid" aria-label="Advertisement">'
            . '<span class="mm-ad-label">ADVERTISEMENT</span>'
            . '<!-- AdSense: mid-article slot -->'
            . '</div>';
        array_splice( $paragraphs, 4, 0, [ $slot ] );
        $content = implode( '</p>', $paragraphs );
    }
    return $content;
}, 20 );

// 6.3 Single post: end-of-article ad slot
add_action( 'generate_after_entry_content', function() {
    if ( ! is_single() || is_page() || ! MACROMALT_ADSENSE_ACTIVE ) {
        return;
    }
    echo '<div class="mm-ad-slot mm-ad-end" aria-label="Advertisement">'
        . '<span class="mm-ad-label">ADVERTISEMENT</span>'
        . '<!-- AdSense: end-of-article slot -->'
        . '</div>';
}, 10 );

// ads.txt NOTE: place at WordPress site root (not in theme).
// Template: "google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0"
// Deploy path: /public_html/ads.txt (or equivalent root directory)
?>
