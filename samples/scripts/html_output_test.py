#!/usr/bin/env python3

text = '''
<div style="clear: both;margin: 0 auto;width: 800px;color: #000305;">
<header id="banner" class="body" style="margin: 0 auto; padding: 2.5em 0 0 0;">
  <h1 style="font-size: 3.571em; line-height: 1.2;">
    <a href="https://www.smashingmagazine.com/">Smashing HTML5! <strong>HTML5 in the year <del>2022</del> <ins>2009</ins></strong></a>
  </h1>

  <nav style="background: #000305; font-size: 1.143em; height: 40px; line-height: 30px; margin: 3em auto 2em auto; 
              padding: 0; text-align: center; width: 800px; border-radius: 5px;">
    <ul style="list-style: none; margin: 0 auto; width: 800px;list-style: outside disc;">
        <li style="float: left; display: inline; line-height: 2.7em; margin: 0;background-color:#C74350; width: 80px;
                   color: #fff;border-top-left-radius: 5px;border-bottom-left-radius: 5px;" class="active" >
            <a href="https://www.smashingmagazine.com/" style="outline: 0;color: #fff;">home</a>
        </li>
        <li style="outline: 0; float: left; display: inline; line-height: 2.7em; margin-left: 1em;">
            <a style="color: #fff;" href="https://www.smashingmagazine.com/">portfolio</a>
        </li>
    
        <li style="outline: 0; float: left; display: inline; line-height: 2.7em; margin-left: 1em;color: #fff;">
            <a style="color: #fff;" href="https://www.smashingmagazine.com/">blog</a>
        </li>
        <li style="outline: 0; float: left; display: inline; line-height: 2.7em; margin-left: 1em;color: #fff;">
            <a style="color: #fff;" href="https://www.smashingmagazine.com/">contact</a>
        </li>
    </ul>
  </nav>

</header><!-- /#banner -->  

<aside id="featured" class="body" style="display: block;background: #fff;margin-bottom: 2em;padding: 20px; 
                                         width: 760px;border-radius: 10px;"><article style="display:block">
  <figure style="display: block; float: right;border: 2px solid #eee;margin: 0.786em 2em 0 5em;">
    <img width="248" src="https://europeandesign.s3.amazonaws.com/uploads/2014/02/smashing-1100x616.png" alt="Smashing Magazine" />
  </figure>
  <hgroup>

    <h2 style="color: #C74451; font-size: 1.714em; margin-bottom: 0.333em;">Featured Article</h2>
    <h3 style="font-size: 1.429em; margin-bottom: .5em;"><a href="https://www.smashingmagazine.com/">HTML5 in Smashing Magazine!</a></h3>
  </hgroup>
  <p>Discover how to use Graceful Degradation and Progressive Enhancement techniques to achieve an outstanding, 
     cross-browser <a href="http://dev.w3.org/html5/spec/Overview.html" rel="external">HTML5</a> and 
     <a href="http://www.w3.org/TR/css3-roadmap/" rel="external">CSS3</a> website today!
  </p>

</article></aside><!-- /#featured -->

<section id="content" class="body" style="background: #fff; margin-bottom: 2em; overflow: hidden; padding: 20px 20px; 
                                          width: 760px; border-radius: 10px; -moz-border-radius: 10px;">
  <ol id="posts-list" class="hfeed" style="list-style: none; margin: 1em 0 1.5em 1.5em;">
    <li><article style="display:block" class="hentry">  
      <header style="">
        <h2 class="entry-title" style="font-size: 1.5em">
            <a style="color: #C74350" href="https://www.smashingmagazine.com/" rel="bookmark" title="Permalink to this POST TITLE">This be the title</a>
        </h2>

      </header>

      <footer class="post-info">
        <abbr class="published" title="2005-10-10T14:07:00-07:00"><!-- YYYYMMDDThh:mm:ss+ZZZZ -->
          10th October 2005
        </abbr>

        <address class="vcard author">

          By <a class="url fn" href="https://www.smashingmagazine.com/">Enrique Ramírez</a>
        </address>
      </footer><!-- /.post-info -->

      <div class="entry-content">

        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque venenatis nunc vitae libero iaculis elementum. Nullam et justo <a href="https://www.smashingmagazine.com/">non sapien</a> dapibus blandit nec et leo. Ut ut malesuada tellus.</p>
      </div><!-- /.entry-content -->
    </article></li>

    <li><article style="display:block" class="hentry">
      ...
    </article></li>

    <li><article style="display:block" class="hentry">
      ...
    </article></li>

  </ol><!-- /#posts-list -->
</section><!-- /#content -->

<section id="extras" class="body" style="margin: 0 auto 3em auto; overflow: hidden;">
  <div class="blogroll" style="float: left; width: 615px;">
    <h2 style="color: #C74350; font-size: 1.429em; margin-bottom: .25em; padding: 0 3px;">blogroll</h2>

    <ul style="list-style: none; margin: 0;">
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">HTML5 Doctor</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">HTML5 Spec (working draft)</a>
      </li>

      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Smashing Magazine</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">W3C</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Wordpress</a>
      </li>

      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Wikipedia</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">HTML5 Doctor</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">HTML5 Spec (working draft)</a>
      </li>

      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Smashing Magazine</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">W3C</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Wordpress</a>
      </li>

      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Wikipedia</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">HTML5 Doctor</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">HTML5 Spec (working draft)</a>
      </li>

      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Smashing Magazine</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">W3C</a>
      </li>
      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Wordpress</a>
      </li>

      <li style="float: left; margin: 0 20px 0 0; width: 185px;
                 border-bottom: 1px solid #fff;">
            <a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                      padding: .3em .25em;" href="https://www.smashingmagazine.com/" rel="external">Wikipedia</a>
      </li>
    </ul>
  </div><!-- /.blogroll -->

  <div class="social" style="float: right; width: 175px;">

    <h2 style="color: #C74350; font-size: 1.429em; margin-bottom: .25em; padding: 0 3px;">social</h2>
    <ul  style="list-style: none; margin: 0;">
      <li style="border-bottom: 1px solid #fff;"><a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                padding: .3em .25em;" href="http://delicious.com/enrique_ramirez" rel="me">delicious</a></li>
      <li style="border-bottom: 1px solid #fff;"><a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                padding: .3em .25em;" href="http://digg.com/users/enriqueramirez" rel="me">digg</a></li>

      <li style="border-bottom: 1px solid #fff;"><a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                padding: .3em .25em;" href="http://facebook.com/enrique.ramirez.velez" rel="me">facebook</a></li>
      <li style="border-bottom: 1px solid #fff;"><a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                padding: .3em .25em;" href="http://www.lastfm.es/user/enrique-ramirez" rel="me">last.fm</a></li>
      <li style="border-bottom: 1px solid #fff;"><a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                padding: .3em .25em;" href="http://website.com/feed/" rel="alternate">rss</a></li>

      <li style="border-bottom: 1px solid #fff;"><a style="color: #444; display: block; border-bottom: 1px solid #F4E3E3; text-decoration: none; 
                padding: .3em .25em;" href="http://twitter.com/enrique_ramirez" rel="me">twitter</a></li>
    </ul>
  </div><!-- /.social -->
</section><!-- /#extras -->

'''

print(text)
